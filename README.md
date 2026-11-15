# Ground Effect Lab

How much battery mass does flying near the surface actually save?

This study solves the span loading of a finite wing above a slip plane, then
closes the mission energy balance with battery mass included in aircraft weight.
For the supplied 60 km case, h/b=0.1 gives 43.8% less induced drag at fixed lift
and 10.2% less battery mass: 35.58 kg instead of 39.63 kg. Profile drag, reserve
energy and propulsion losses account for the smaller mission benefit.

![Height sweep, mass closure, span loading and input sensitivity](results/study.png)

The [calculation](results/report.md) lists the assumed inputs and feasibility
screens. [convergence.csv](results/convergence.csv) shows the remaining spanwise
mesh dependence; [sensitivity.csv](results/sensitivity.csv) shows how much the
answer moves when drag, headwind or pack specific energy changes.

## Reproduce or change the case

Python 3.10+ and NumPy; Matplotlib is needed for the plots.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install -e .
make test
make study
python examples/study.py --config examples/coastal.json --output /tmp/coastal-study
```

Start with [coastal.json](examples/coastal.json). Dry mass includes payload and
all hardware except the pack. Wh/kg is a pack value. Reserve time adds flight
energy, while usable fraction limits stored energy. The quadratic can have no
positive mass closure; those cases retain their failure reasons in the report.
Motor power, gross mass and the assumed CL ceiling are checked separately.

## Model boundary

The code uses discrete lifting-line theory, constant section lift slope and a
straight wake with mirrored circulation. It resolves span loading; chordwise
ground effect, separation, waves, hull resistance and pitch/heave stability are
outside the model. The launch-energy allowance needs an independent takeoff
power calculation.

The example is a numerical comparison using assumed craft data. The next useful
validation is a fixed-lift drag measurement across heights.

[Equations](docs/model.md) · [Verification](docs/verification.md) ·
[Calculation notes](docs/review.md) · [Source hashes](results/provenance.json)
