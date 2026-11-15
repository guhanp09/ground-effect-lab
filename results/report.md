# Mission result

Input: `coastal.json`; SHA-256 `6a823c161cd6ca54c8a6a9980c1d4d780cdfbcf721d96c26dc0b838be0a706d3`.
All craft and pack inputs are assumptions.

| Input | Value |
| --- | ---: |
| Dry mass, including payload | 180 kg |
| Distance | 60 km |
| True airspeed / headwind | 30 / 4 m/s |
| Non-induced CD | 0.032 |
| Propulsion efficiency | 0.72 |
| Pack specific energy | 190 Wh/kg |
| Usable stored energy | 80% |
| Extra cruise time for reserve | 300 s |
| Launch energy allowance | 350 Wh |

At fixed lift, induced drag at h/b=0.1 is 43.8% below free air.
Battery mass at h/b=0.1 is 35.58 kg, versus 39.63 kg in free air (10.2% lower). The table below lists the feasibility screens separately.

| h/b | Battery mass [kg] | Screening result |
| --- | ---: | --- |
| 0.05 | 34.20 | pass |
| 0.1 | 35.58 | pass |
| 0.2 | 37.16 | pass |
| 0.5 | 38.81 | pass |
| 1.0 | 39.37 | pass |
| free | 39.63 | pass |

The 96-to-192-panel CDi change at h/b=0.1 is 0.758%.
`convergence.csv` continues to 384 panels. These measure discretization error;
they do not quantify the physical error of the lifting-line or slip-plane model.

`sensitivity.csv` changes one input at a time and retains failure reasons.
Hatching marks infeasible mass solutions in the plot. Reserve time adds cruise
energy; usable fraction limits the stored pack energy available to the mission.
Launch energy does not check takeoff power or hull resistance.
