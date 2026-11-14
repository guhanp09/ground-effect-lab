# Coastal mission calculation

Numerical predictions from `examples/coastal.json`; no measured craft data.
Input SHA-256: `6a823c161cd6ca54c8a6a9980c1d4d780cdfbcf721d96c26dc0b838be0a706d3`.

At h/b = 0.1 the lifting-line model predicts **43.8% less induced drag
at fixed lift** than free air. The coupled mission needs **35.58 kg**
of battery versus **39.63 kg** in free air, a **10.2%**
reduction. Profile drag, hotel load, launch allowance and reserve are retained.
This is a model comparison, not an achievable range claim.

At that point the electrical cruise demand is 6.98 kW,
gross mass is 215.58 kg and required CL is 0.479.
The prescribed motor, gross-mass and CL screens pass.
Launch power, propeller limits and water takeoff feasibility have not been checked.

The 96-to-192-panel induced-drag change at h/b=0.1 is 0.758%.
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
