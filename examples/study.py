"""Regenerate the checked-in numerical study from any working directory."""

from dataclasses import replace
import argparse
from pathlib import Path
import platform
import importlib.metadata
import csv
import hashlib
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ground-effect-mpl")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ground_effect_lab.lifting_line import Wing, fixed_lift
from ground_effect_lab.mission import Mission, size_battery


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def record_provenance():
    paths = []
    for directory in ("src", "examples"):
        paths.extend(
            p
            for p in (ROOT / directory).rglob("*")
            if p.suffix in (".py", ".json") and "__pycache__" not in p.parts
        )
    record = {
        "data_status": "numerical or synthetic; no physical measurements",
        "python": platform.python_version(),
        "numpy": importlib.metadata.version("numpy"),
        "matplotlib": importlib.metadata.version("matplotlib"),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)
        },
    }
    return record


def run_study(source, out):
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads(source.read_text())
    wing, mission = Wing(**config["wing"]), Mission(**config["mission"])
    if wing.area_m2 != mission.area_m2:
        raise ValueError("Wing and mission reference areas differ")
    heights = [0.05, 0.1, 0.2, 0.5, 1.0, None]
    rows = []
    for ratio in heights:
        height = None if ratio is None else ratio * wing.span_m
        coarse = fixed_lift(wing, 0.6, height, 96)
        fine = fixed_lift(wing, 0.6, height, 192)
        k = fine.cdi / fine.cl**2
        result = size_battery(mission, k)
        rows.append(
            {
                "height_span_ratio": "free" if ratio is None else ratio,
                "alpha_deg_at_cl_0_6": np.degrees(fine.alpha_rad),
                "induced_k": k,
                "cdi_at_cl_0_6": fine.cdi,
                "mesh_change_pct": 100 * abs(fine.cdi / coarse.cdi - 1),
                "reason": "; ".join(result["reasons"]),
                **{
                    key: result.get(key, "")
                    for key in (
                        "battery_mass_kg",
                        "gross_mass_kg",
                        "electrical_power_w",
                        "cl",
                        "feasible",
                    )
                },
            }
        )
    write_csv(out / "height_sweep.csv", rows)
    convergence = []
    for n in (24, 48, 96, 192, 384):
        s = fixed_lift(wing, 0.6, wing.span_m * 0.1, n)
        convergence.append(
            {"panels": n, "alpha_deg": np.degrees(s.alpha_rad), "cdi": s.cdi}
        )
    write_csv(out / "convergence.csv", convergence)
    base = rows[1]
    k = base["induced_k"]
    sensitivities = []
    changes = [
        ("profile_cd", 0.024, 0.040),
        ("headwind_m_s", 0, 8),
        ("propulsion_efficiency", 0.64, 0.80),
        ("battery_wh_kg", 160, 220),
        ("launch_energy_wh", 175, 700),
    ]
    for key, lo, hi in changes:
        for val in (lo, hi):
            try:
                r = size_battery(replace(mission, **{key: val}), k)
            except ValueError as error:
                r = {"feasible": False, "reasons": [str(error)]}
            sensitivities.append(
                {
                    "parameter": key,
                    "value": val,
                    "feasible": r["feasible"],
                    "battery_mass_kg": r.get("battery_mass_kg", ""),
                    "reason": "; ".join(r["reasons"]),
                }
            )
    write_csv(out / "sensitivity.csv", sensitivities)
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    labels = [str(r) if r is not None else "Free air" for r in heights]
    axes[0, 0].plot(labels, [r["induced_k"] for r in rows], "o-", color="#156b7a")
    axes[0, 0].set(
        xlabel="Height / span",
        ylabel="Induced drag factor k",
        title="Same lift, different induced drag",
    )
    masses = [
        r["battery_mass_kg"] if r["battery_mass_kg"] != "" else np.nan for r in rows
    ]
    bars = axes[0, 1].bar(
        labels, masses, color=["#156b7a" if r["feasible"] else "#b66b36" for r in rows]
    )
    for bar, row in zip(bars, rows):
        if not row["feasible"]:
            bar.set_hatch("//")
            axes[0, 1].text(
                bar.get_x() + bar.get_width() / 2,
                0,
                "infeasible",
                rotation=90,
                ha="center",
                va="bottom",
                fontsize=8,
            )
    axes[0, 1].set(
        ylabel="Battery mass [kg]",
        xlabel="Height / span",
        title="Mass includes its own energy penalty",
    )
    s = fixed_lift(wing, 0.6, wing.span_m * 0.1, 192)
    axes[1, 0].plot(s.y_m, 2 * s.circulation_m2_s / s.chord_m, color="#156b7a")
    axes[1, 0].set(
        xlabel="Spanwise station [m]",
        ylabel="Section lift coefficient",
        title="Span loading at CL = 0.6, h/b = 0.1",
    )
    names, deltas = [], []
    for r in sensitivities:
        status = "" if r["feasible"] else " (infeasible)"
        names.append(f"{r['parameter']} = {r['value']}{status}")
        if r["battery_mass_kg"] != "" and base["battery_mass_kg"] != "":
            deltas.append(r["battery_mass_kg"] - base["battery_mass_kg"])
        else:
            deltas.append(np.nan)
    axes[1, 1].barh(
        names, deltas, color=["#b66b36" if d > 0 else "#156b7a" for d in deltas]
    )
    axes[1, 1].axvline(0, color="#555", lw=0.8)
    axes[1, 1].tick_params(axis="y", labelsize=8)
    axes[1, 1].set(
        xlabel="Change in battery mass [kg]",
        title="Assumed inputs can dominate the gain",
    )
    fig.suptitle(
        "Ground Effect Lab · idealized lifting line + assumed coastal mission",
        fontsize=14,
    )
    fig.savefig(out / "study.png", dpi=170)
    plt.close(fig)
    free = rows[-1]
    drag_reduction = 100 * (1 - k / free["induced_k"])
    comparison = "Battery-mass comparison unavailable: no positive energy/mass closure in one or both cases."
    if base["battery_mass_kg"] != "" and free["battery_mass_kg"] != "":
        reduction = 100 * (1 - base["battery_mass_kg"] / free["battery_mass_kg"])
        comparison = (
            f"Battery mass at h/b=0.1 is {base['battery_mass_kg']:.2f} kg, versus "
            f"{free['battery_mass_kg']:.2f} kg in free air ({reduction:.1f}% lower). "
            "The table below lists the feasibility screens separately."
        )
    report = f"""# Mission result

Input: `{source.name}`; SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`.
All craft and pack inputs are assumptions.

| Input | Value |
| --- | ---: |
| Dry mass, including payload | {mission.dry_mass_kg:g} kg |
| Distance | {mission.distance_km:g} km |
| True airspeed / headwind | {mission.speed_m_s:g} / {mission.headwind_m_s:g} m/s |
| Non-induced CD | {mission.profile_cd:g} |
| Propulsion efficiency | {mission.propulsion_efficiency:g} |
| Pack specific energy | {mission.battery_wh_kg:g} Wh/kg |
| Usable stored energy | {100*mission.usable_fraction:g}% |
| Extra cruise time for reserve | {mission.reserve_time_s:g} s |
| Launch energy allowance | {mission.launch_energy_wh:g} Wh |

At fixed lift, induced drag at h/b=0.1 is {drag_reduction:.1f}% below free air.
{comparison}

| h/b | Battery mass [kg] | Screening result |
| --- | ---: | --- |
"""
    for row in rows:
        mass = (
            f"{row['battery_mass_kg']:.2f}"
            if row["battery_mass_kg"] != ""
            else "no closure"
        )
        report += (
            f"| {row['height_span_ratio']} | {mass} | {row['reason'] or 'pass'} |\n"
        )
    report += f"""
The 96-to-192-panel CDi change at h/b=0.1 is {base['mesh_change_pct']:.3f}%.
`convergence.csv` continues to 384 panels. These measure discretization error;
they do not quantify the physical error of the lifting-line or slip-plane model.

`sensitivity.csv` changes one input at a time and retains failure reasons.
Hatching marks infeasible mass solutions in the plot. Reserve time adds cruise
energy; usable fraction limits the stored pack energy available to the mission.
Launch energy does not check takeoff power or hull resistance.
"""
    (out / "report.md").write_text(report)
    provenance = record_provenance()
    provenance["mission_input"] = {
        "file": source.name,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(report)


def main():
    parser = argparse.ArgumentParser(
        description="Compare fixed-lift ground effect and mission energy."
    )
    parser.add_argument("--config", type=Path, default=ROOT / "examples/coastal.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    run_study(args.config, args.output)


if __name__ == "__main__":
    main()
