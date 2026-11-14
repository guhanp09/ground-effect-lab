# Verification evidence

`python -m pytest -q` checks:

| Check | Independent expectation |
| --- | --- |
| Elliptic wing, free-air lift slope | a0/(1+a0/(pi AR)), within 0.5% at 256 panels |
| Elliptic wing, fixed-lift induced drag | CL²/(pi AR), within 1.2%; errors reduce with refinement |
| Image boundary | Normal wake velocity at z=0 cancels to roundoff |
| Far-height limit | h=1000 spans approaches the free-air coefficient |
| Scaling | Doubling alpha doubles CL and quadruples CDi |
| Height sweep | Positive induced drag, increasing with height at fixed CL |
| Battery closure | Independent drag/power integration recovers stored usable energy |
| Bad or impossible inputs | Invalid geometry, nonpositive groundspeed, no energy closure and motor overload are surfaced |

`results/convergence.csv` refines the rectangular-wing h/b=0.1 case from 24 to
384 panels. The study uses 192 panels for reported mission results. The remaining
discretization error must not be confused with uncertainty in the physics.

Missing evidence: wind-tunnel or tow measurements, a chord-resolved aerodynamic
comparison, free-surface effects, Reynolds-number-dependent profile drag and
an experimentally supported whole-craft mass/drag breakdown. These are follow-up
work items; the numerical tests do not replace them.
