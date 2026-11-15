import math
from dataclasses import replace
import numpy as np
import pytest
from ground_effect_lab.lifting_line import Wing, solve, fixed_lift, wake_matrix
from ground_effect_lab.mission import Mission, size_battery


def test_elliptical_wing_against_prandtl_solution():
    wing = Wing(8, 8, "elliptical")
    s = solve(wing, math.radians(4), panels=256)
    slope = 2 * math.pi / (1 + 2 / wing.aspect_ratio)
    assert s.cl / math.radians(4) == pytest.approx(slope, rel=0.005)
    assert s.cdi == pytest.approx(s.cl**2 / (math.pi * wing.aspect_ratio), rel=0.012)


def test_mesh_converges_to_elliptical_analytic_drag():
    wing = Wing(8, 8, "elliptical")
    expected = 0.6**2 / (math.pi * wing.aspect_ratio)
    errors = [
        abs(fixed_lift(wing, 0.6, panels=n).cdi - expected) for n in (32, 64, 128, 256)
    ]
    assert all(b < a for a, b in zip(errors, errors[1:]))


def test_image_satisfies_wall_and_far_height_recovers_free_air():
    wing = Wing(8, 8)
    edges, _, _ = wing.mesh(64)
    y = np.linspace(-3.9, 3.9, 55)
    assert np.max(abs(wake_matrix(y, np.zeros_like(y), edges, 0.8))) < 1e-14
    a = fixed_lift(wing, 0.6)
    b = fixed_lift(wing, 0.6, 8000)
    assert b.cdi == pytest.approx(a.cdi, rel=1e-6)


def test_fixed_lift_height_sweep_and_linear_scaling():
    wing = Wing(8, 8)
    heights = (0.2, 0.4, 0.8, 1.6, 8.0)
    sols = [fixed_lift(wing, 0.6, h) for h in heights]
    assert all(s.cl == pytest.approx(0.6) and s.cdi > 0 for s in sols)
    assert all(b.cdi > a.cdi for a, b in zip(sols, sols[1:]))
    a, b = solve(wing, 0.03), solve(wing, 0.06)
    assert b.cl == pytest.approx(2 * a.cl)
    assert b.cdi == pytest.approx(4 * a.cdi)
    assert a.residual < 1e-12


def test_mass_closure_and_independent_energy_balance():
    m = Mission()
    r = size_battery(m, 0.03)
    assert r["feasible"]
    q = 0.5 * m.rho_kg_m3 * m.speed_m_s**2
    drag = q * m.area_m2 * (m.profile_cd + 0.03 * r["cl"] ** 2)
    power = drag * m.speed_m_s / m.propulsion_efficiency + m.hotel_power_w
    energy = power * (60000 / 26 + 300) / 3600 + 350
    assert energy == pytest.approx(r["battery_mass_kg"] * 190 * 0.8)
    assert abs(r["closure_error_wh"]) < 1e-8
    assert r["feedback_slope"] < 1


def test_infeasibility_is_not_hidden():
    assert not size_battery(replace(Mission(), distance_km=10000), 0.04)["feasible"]
    r = size_battery(replace(Mission(), motor_limit_w=100), 0.03)
    assert not r["feasible"] and "motor" in r["reasons"][0]
    with pytest.raises(ValueError):
        Mission(headwind_m_s=30)


def test_hotel_load_is_in_energy_but_not_motor_rating():
    mission = replace(Mission(), hotel_power_w=2000)
    base = size_battery(mission, 0.03)
    motor_limit = base["propulsion_electrical_power_w"] + 1
    result = size_battery(replace(mission, motor_limit_w=motor_limit), 0.03)
    assert result["feasible"]
    assert result["electrical_power_w"] > motor_limit
    assert result["propulsion_electrical_power_w"] < motor_limit


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_bad_geometry_rejected(bad):
    with pytest.raises(ValueError):
        Wing(bad, 8)
    with pytest.raises(ValueError):
        solve(Wing(8, 8), 0.05, height_m=bad)
