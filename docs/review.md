# Calculation notes

## Compare at the same lift

Holding incidence fixed while lowering the wing changes both lift and drag.
The height study therefore solves for CL=0.6 at every height. The free-air
elliptical wing provides a separate analytical check on lift slope and induced
drag. A vanishing wall-normal wake velocity checks the image signs; it does
not establish that a flat slip plane represents a water surface.

The 192-panel result still has measurable mesh error. The 384-panel point stays
in the output rather than treating a small linear-system residual as evidence
that the aerodynamic discretization is accurate.

## Close the mass balance

Adding battery increases required lift and induced drag. The lower positive
quadratic root gives the low-mass branch; the larger root has unstable mass/energy
feedback. A missing root is an engineering result, so the plotting and report
code now preserve that failure instead of attempting arithmetic on an empty mass.

Hotel load belongs in pack energy and total electrical demand. An earlier motor
screen also counted it against the motor rating; the current screen uses
propulsion electrical demand only. A high-hotel-load test covers that distinction.

## Keep report text tied to inputs

Reserve duration and usable fraction are read from the case file and printed
in the input table. Command-level tests change both values and run a 10,000 km
case that has no mass closure. This catches stale example prose and failure paths
that the default 60 km case cannot exercise.

The dominant unresolved inputs are whole-craft profile drag and pack-level
specific energy. More panels will not reduce their uncertainty. A measured drag
breakdown, a chord-resolved comparison and longitudinal stability work are the
next steps before using the result to size a craft.
