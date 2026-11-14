"""Regenerate the checked-in numerical study from any working directory."""

from dataclasses import replace
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
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ground-effect-mpl"))
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
    for directory in ('src', 'include', 'examples', 'tools', 'cad'):
        if (ROOT / directory).exists():
            paths.extend(p for p in (ROOT / directory).rglob('*')
                         if p.suffix in ('.py', '.hpp', '.cpp', '.json', '.scad')
                         and '__pycache__' not in p.parts)
    record = {
        'data_status': 'numerical or synthetic; no physical measurements',
        'python': platform.python_version(),
        'numpy': importlib.metadata.version('numpy'),
        'matplotlib': importlib.metadata.version('matplotlib'),
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(paths)},
    }
    (ROOT / 'results/provenance.json').write_text(json.dumps(record, indent=2) + '\n')


def main():
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    source = ROOT / "examples/coastal.json"
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
        k = fine.cdi / fine.cl ** 2
        result = size_battery(mission, k)
        rows.append({"height_span_ratio": "free" if ratio is None else ratio,
                     "alpha_deg_at_cl_0_6": np.degrees(fine.alpha_rad),
                     "induced_k": k, "cdi_at_cl_0_6": fine.cdi,
                     "mesh_change_pct": 100 * abs(fine.cdi / coarse.cdi - 1),
                     **{key: result.get(key, "") for key in
                        ("battery_mass_kg", "gross_mass_kg", "electrical_power_w", "cl", "feasible")}})
    write_csv(out / "height_sweep.csv", rows)
    convergence = []
    for n in (24, 48, 96, 192, 384):
        s = fixed_lift(wing, 0.6, wing.span_m * 0.1, n)
        convergence.append({"panels": n, "alpha_deg": np.degrees(s.alpha_rad), "cdi": s.cdi})
    write_csv(out / "convergence.csv", convergence)
    base = rows[1]
    k = base["induced_k"]
    sensitivities = []
    changes = [("profile_cd", 0.024, 0.040), ("headwind_m_s", 0, 8),
               ("propulsion_efficiency", 0.64, 0.80), ("battery_wh_kg", 160, 220),
               ("launch_energy_wh", 175, 700)]
    for key, lo, hi in changes:
        for val in (lo, hi):
            r = size_battery(replace(mission, **{key: val}), k)
            sensitivities.append({"parameter": key, "value": val, "feasible": r["feasible"],
                                  "battery_mass_kg": r.get("battery_mass_kg", ""),
                                  "reason": "; ".join(r["reasons"])})
    write_csv(out / "sensitivity.csv", sensitivities)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    labels = [str(r) if r is not None else "Free air" for r in heights]
    axes[0, 0].plot(labels, [r["induced_k"] for r in rows], "o-", color="#156b7a")
    axes[0, 0].set(xlabel="Height / span", ylabel="Induced drag factor k", title="Same lift, different induced drag")
    axes[0, 1].bar(labels, [r["battery_mass_kg"] for r in rows], color="#156b7a")
    axes[0, 1].set(ylabel="Battery mass [kg]", xlabel="Height / span", title="Mass includes its own energy penalty")
    s = fixed_lift(wing, 0.6, wing.span_m * 0.1, 192)
    axes[1, 0].plot(s.y_m, 2 * s.circulation_m2_s / s.chord_m, color="#156b7a")
    axes[1, 0].set(xlabel="Spanwise station [m]", ylabel="Section lift coefficient", title="Span loading at CL = 0.6, h/b = 0.1")
    names, deltas = [], []
    for r in sensitivities:
        names.append(f"{r['parameter']} = {r['value']}")
        deltas.append(r["battery_mass_kg"] - base["battery_mass_kg"])
    axes[1, 1].barh(names, deltas, color=["#b66b36" if d > 0 else "#156b7a" for d in deltas])
    axes[1, 1].axvline(0, color="#555", lw=0.8)
    axes[1, 1].tick_params(axis="y", labelsize=8)
    axes[1, 1].set(xlabel="Change in battery mass [kg]", title="Assumed inputs can dominate the gain")
    fig.suptitle("Ground Effect Lab · idealized lifting line + assumed coastal mission", fontsize=14)
    fig.savefig(out / "study.png", dpi=170)
    plt.close(fig)
    free = rows[-1]
    reduction = 100 * (1 - base["battery_mass_kg"] / free["battery_mass_kg"])
    drag_reduction = 100 * (1 - k / free["induced_k"])
    report = f'''# Coastal mission calculation

Numerical predictions from `examples/coastal.json`; no measured craft data.
Input SHA-256: `{hashlib.sha256(source.read_bytes()).hexdigest()}`.

At h/b = 0.1 the lifting-line model predicts **{drag_reduction:.1f}% less induced drag
at fixed lift** than free air. The coupled mission needs **{base['battery_mass_kg']:.2f} kg**
of battery versus **{free['battery_mass_kg']:.2f} kg** in free air, a **{reduction:.1f}%**
reduction. Profile drag, hotel load, launch allowance and reserve are retained.
This is a model comparison, not an achievable range claim.

At that point the electrical cruise demand is {base['electrical_power_w']/1000:.2f} kW,
gross mass is {base['gross_mass_kg']:.2f} kg and required CL is {base['cl']:.3f}.
The prescribed motor, gross-mass and CL screens {'pass' if base['feasible'] else 'fail'}.
Launch power, propeller limits and water takeoff feasibility have not been checked.

The 96-to-192-panel induced-drag change at h/b=0.1 is {base['mesh_change_pct']:.3f}%.
See `convergence.csv` for the further 384-panel point. Convergence measures numerical
discretization error only. It does not validate the straight wake, section lift
slope, slip-plane or lifting-line approximations.

`sensitivity.csv` varies one assumption at a time. Pack Wh/kg is at pack level;
using a cell specification here would understate structural, BMS and wiring mass.
Headwind changes leg time while airspeed remains fixed. Reserve is a separate
five-minute cruise-energy allowance; the 20% unusable battery fraction is not
counted as that reserve. The launch allowance is energy only.

The useful next experiment is a fixed-lift drag comparison across heights, with
independent airspeed and force measurements. A calm-water slip plane cannot
establish wave clearance, pitch/heave stability or free-surface drag.
'''
    (out / "report.md").write_text(report)
    record_provenance()
    print(report)


if __name__ == "__main__":
    main()
