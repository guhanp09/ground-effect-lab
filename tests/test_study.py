"""Exercise the published command with inputs other than the README example."""

import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("distance_km", [60, 10000])
def test_report_tracks_inputs_and_handles_no_mass_closure(tmp_path, distance_km):
    config = json.loads((ROOT / "examples/coastal.json").read_text())
    config["mission"].update(
        distance_km=distance_km, reserve_time_s=90, usable_fraction=0.65
    )
    source = tmp_path / "case.json"
    source.write_text(json.dumps(config))
    output = tmp_path / "result"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples/study.py"),
            "--config",
            str(source),
            "--output",
            str(output),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    report = (output / "report.md").read_text()
    assert "| Extra cruise time for reserve | 90 s |" in report
    assert "| Usable stored energy | 65% |" in report
    with (output / "height_sweep.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    if distance_km == 10000:
        assert all(row["feasible"] == "False" and row["reason"] for row in rows)
        assert "no closure" in report
    else:
        assert all(row["feasible"] == "True" for row in rows)
    assert (output / "study.png").stat().st_size > 0
