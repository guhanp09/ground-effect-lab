"""Battery-mass closure for a steady cruise leg plus explicit energy allowances."""

from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class Mission:
    dry_mass_kg: float = 180.0  # airframe, payload, motor, all except battery
    area_m2: float = 8.0
    speed_m_s: float = 30.0  # true airspeed
    distance_km: float = 60.0
    headwind_m_s: float = 4.0
    profile_cd: float = 0.032  # assumed whole-craft non-induced drag
    propulsion_efficiency: float = 0.72
    battery_wh_kg: float = 190.0  # assumed pack-level, not cell-level
    usable_fraction: float = 0.80
    hotel_power_w: float = 100.0
    launch_energy_wh: float = 350.0  # externally supplied allowance; no hull model
    reserve_time_s: float = 300.0
    motor_limit_w: float = 25000.0
    gross_mass_limit_kg: float = 350.0
    cl_limit: float = 1.0  # assumed screening bound; no stall prediction
    rho_kg_m3: float = 1.225

    def __post_init__(self):
        vals = asdict(self)
        if not all(math.isfinite(v) for v in vals.values()):
            raise ValueError("Mission inputs must be finite")
        positive = (
            "dry_mass_kg",
            "area_m2",
            "speed_m_s",
            "distance_km",
            "battery_wh_kg",
            "motor_limit_w",
            "gross_mass_limit_kg",
            "cl_limit",
            "rho_kg_m3",
        )
        if any(vals[k] <= 0 for k in positive):
            raise ValueError(
                "Masses, geometry, speed, energy density and limits must be positive"
            )
        if not 0 < self.propulsion_efficiency <= 1 or not 0 < self.usable_fraction <= 1:
            raise ValueError("Efficiencies/fractions must lie in (0,1]")
        if any(
            vals[k] < 0
            for k in (
                "profile_cd",
                "hotel_power_w",
                "launch_energy_wh",
                "reserve_time_s",
            )
        ):
            raise ValueError("Drag and energy allowances cannot be negative")
        if self.headwind_m_s >= self.speed_m_s:
            raise ValueError("No positive groundspeed")


def size_battery(mission, induced_k):
    """Solve the quadratic energy/mass feedback and retain the lower-mass root.

    E_required(m_b) = A (m_dry+m_b)^2 + B = m_b e_pack f_usable.
    Report model feasibility separately from algebraic closure.
    """
    m = mission
    if not math.isfinite(induced_k) or induced_k <= 0:
        raise ValueError("Induced drag factor must be positive and finite")
    q = 0.5 * m.rho_kg_m3 * m.speed_m_s**2
    duration = m.distance_km * 1000 / (m.speed_m_s - m.headwind_m_s) + m.reserve_time_s
    power_quadratic = (
        induced_k * 9.80665**2 / (q * m.area_m2) * m.speed_m_s / m.propulsion_efficiency
    )
    power_constant = (
        q * m.area_m2 * m.profile_cd * m.speed_m_s / m.propulsion_efficiency
        + m.hotel_power_w
    )
    a = power_quadratic * duration / 3600
    b = 2 * a * m.dry_mass_kg - m.battery_wh_kg * m.usable_fraction
    c = a * m.dry_mass_kg**2 + power_constant * duration / 3600 + m.launch_energy_wh
    discriminant = b * b - 4 * a * c
    if discriminant < 0 or b >= 0:
        return {"feasible": False, "reasons": ["no positive battery-mass closure"]}
    battery = 2 * c / (-b + math.sqrt(discriminant))
    total = m.dry_mass_kg + battery
    power = power_quadratic * total**2 + power_constant
    cl = total * 9.80665 / (q * m.area_m2)
    required = a * total**2 + power_constant * duration / 3600 + m.launch_energy_wh
    reasons = []
    for invalid, reason in [
        (
            power - m.hotel_power_w > m.motor_limit_w,
            "cruise propulsion electrical power exceeds motor limit",
        ),
        (total > m.gross_mass_limit_kg, "gross mass exceeds limit"),
        (cl > m.cl_limit, "CL exceeds assumed screening bound"),
    ]:
        if invalid:
            reasons.append(reason)
    return {
        "feasible": not reasons,
        "reasons": reasons,
        "battery_mass_kg": battery,
        "gross_mass_kg": total,
        "electrical_power_w": power,
        "propulsion_electrical_power_w": power - m.hotel_power_w,
        "cl": cl,
        "required_energy_wh": required,
        "closure_error_wh": required - battery * m.battery_wh_kg * m.usable_fraction,
        "feedback_slope": 2 * a * total / (m.battery_wh_kg * m.usable_fraction),
    }
