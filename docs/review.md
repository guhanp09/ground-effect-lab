# Technical review

Reviewed after the initial numerical study, 15 November 2026.

| Finding | Resolution / retained limit |
| --- | --- |
| Comparing one incidence at different heights also changes lift | All drag comparisons use fixed CL |
| A single multiplier could obscure the model | Explicit circulation influence matrix and image terms; equations and limiting tests retained |
| Grid convergence could be mistaken for validation | Analytical elliptic-wing limit, wall residual and refinement are reported separately from missing physical measurements |
| Battery mass was liable to be treated as a free input | Implicit energy/mass closure, stable lower root, feedback slope and infeasibility handling |
| Motor check included hotel power | Corrected to propulsion electrical power; a high-hotel-load regression check exercises the difference |
| Battery energy density could silently mean cell specification | Pack-level assumption and usable fraction are explicit |
| An impressive induced-drag percentage could overstate mission benefit | Both drag and battery-mass reductions lead the README; profile-drag uncertainty is shown beside them |
| Launch energy could imply takeoff feasibility | Report distinguishes energy allowance from unmodelled launch power and hull dynamics |

The core uses one numerical dependency. Inputs have finite/range checks, the
example has an input hash, and study paths resolve independently of the current
directory. Tests exercise analytical limits and physically meaningful failures
rather than copying expected outputs from the implementation.

Unresolved: chordwise ground effect, water-surface dynamics, stability,
whole-craft drag and measured validation. The close-height predictions remain
low-order model comparisons. No certification or fabricated testing is claimed.
