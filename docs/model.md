# Model and conventions

All quantities are SI except the explicitly named Wh, km and degree fields.
The x axis follows the freestream, y is spanwise and z is up. Positive Gamma
produces positive lift; negative w is downwash. Wing area is full-span area.

For strip j with edges yL and yR, its wake contribution at station yi, z=h is

```text
W_ij = 1/(4 pi) [1/(yi-yR) - 1/(yi-yL)
                 - (yi-yR)/((yi-yR)^2 + 4h^2)
                 + (yi-yL)/((yi-yL)^2 + 4h^2)]
w = W Gamma
```

The first two terms are real trailing legs. The latter terms are the reversed
image circulation at z=-h. Free air omits the image. The bound line's vertical
self-velocity is absent in this lifting-line idealization. The wake's normal
velocity cancels at z=0. The implementation does not model wing chord geometry
or a pressure distribution over chord.

The section relation and total coefficients are

```text
2 Gamma_i/(U c_i) = a0 (alpha + w_i/U)
[diag(2/(c a0)) - W] Gamma = U alpha
CL  =  2 sum(Gamma_i dy_i)/(U S)
CDi = -2 sum(Gamma_i w_i dy_i)/(U^2 S)
k   = CDi/CL^2
```

The straight wake makes the problem linear. Fixed lift is obtained by scaling
alpha and resolving, not by comparing different heights at one incidence.
For an elliptic wing in free air, lifting-line theory supplies an independent
benchmark: a = a0/(1+a0/(pi AR)) and CDi=CL²/(pi AR).

## Energy closure

For total mass M = m_dry + m_battery,

```text
q = rho U^2/2
CL = M g/(q S)
P_electrical = [q S CD0 + k (M g)^2/(q S)] U/eta + P_hotel
t = distance/(U-headwind) + reserve_time
E_required = P_electrical t/3600 + launch_energy_Wh
E_available = m_battery * pack_Wh_per_kg * usable_fraction
```

Equating these yields a quadratic. The smaller positive root is retained; the
larger root lies on the high-mass branch where adding battery increases the
required energy faster than the available energy. The report exposes the
feedback slope. No real positive root means no closure under these assumptions.
The stable quadratic expression avoids subtracting nearly equal numbers.

The constant cruise state ignores energy-dependent battery voltage and thermal
limits. Dry mass is an input, not an optimized structure or a demonstrated mass
breakdown. Reserve time and usable fraction have different meanings: one is
explicit extra flight energy; the other caps usable stored pack energy.

## Reference

[Drela and Youngren, AVL User Primer](https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf)
describes related vortex-sheet methods, image planes, induced-drag treatment
and small-angle limitations. This repository is an independent discrete
lifting-line implementation, not AVL, and does not claim an AVL comparison.
