"""Discrete Prandtl lifting line with opposite-sign slip-plane images.

Axes: x downstream, y spanwise, z up. Positive circulation gives positive lift.
The wake is straight, semi-infinite and parallel to x. All bound segments lie
on one horizontal line at z=height. This is not a free-surface flow model.
"""

from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Wing:
    span_m: float
    area_m2: float
    planform: str = "rectangular"
    section_slope_per_rad: float = 2 * math.pi

    def __post_init__(self):
        if not all(math.isfinite(x) and x > 0 for x in
                   (self.span_m, self.area_m2, self.section_slope_per_rad)):
            raise ValueError("Wing dimensions and section slope must be positive and finite")
        if self.planform not in ("rectangular", "elliptical"):
            raise ValueError("Supported planforms: rectangular, elliptical")

    @property
    def aspect_ratio(self):
        return self.span_m ** 2 / self.area_m2

    def mesh(self, panels):
        if not isinstance(panels, int) or not 8 <= panels <= 1024:
            raise ValueError("Use 8 to 1024 spanwise panels")
        edges = -0.5 * self.span_m * np.cos(np.linspace(0, np.pi, panels + 1))
        y = (edges[:-1] + edges[1:]) / 2
        if self.planform == "rectangular":
            chord = np.full(panels, self.area_m2 / self.span_m)
        else:
            chord = 4 * self.area_m2 / (np.pi * self.span_m) * np.sqrt(
                1 - (2 * y / self.span_m) ** 2)
        return edges, y, chord


def wake_matrix(y, z, edges, height):
    """Vertical velocity per unit strip circulation in the x=0 wake plane."""
    dy_right = np.asarray(y)[:, None] - edges[None, 1:]
    dy_left = np.asarray(y)[:, None] - edges[None, :-1]
    dz = np.asarray(z)[:, None] - height
    w = dy_right / (dy_right ** 2 + dz ** 2) - dy_left / (dy_left ** 2 + dz ** 2)
    if math.isfinite(height):
        dz_image = np.asarray(z)[:, None] + height
        w -= (dy_right / (dy_right ** 2 + dz_image ** 2)
              - dy_left / (dy_left ** 2 + dz_image ** 2))
    return w / (4 * np.pi)


@dataclass
class Solution:
    y_m: np.ndarray
    chord_m: np.ndarray
    dy_m: np.ndarray
    circulation_m2_s: np.ndarray
    downwash_m_s: np.ndarray
    alpha_rad: float
    cl: float
    cdi: float
    residual: float


def solve(wing, alpha_rad, height_m=None, panels=96, speed_m_s=1.0):
    """Solve section lift compatibility, not a fitted ground-effect multiplier.

    2 Gamma/(U c) = a0 (alpha + w/U), w = W Gamma.
    CDi = -2 integral(Gamma w dy)/(U^2 S). Profile drag is separate.
    None selects free air; a finite height must be positive.
    """
    if not math.isfinite(alpha_rad) or abs(alpha_rad) > math.radians(15):
        raise ValueError("Linear model requires |alpha| <= 15 degrees")
    if not math.isfinite(speed_m_s) or speed_m_s <= 0:
        raise ValueError("Speed must be positive and finite")
    if height_m is not None and (not math.isfinite(height_m) or height_m <= 0):
        raise ValueError("Height must be positive and finite, or None for free air")
    edges, y, chord = wing.mesh(panels)
    if height_m is None:
        # Free-air wake at its lifting line: no image, dz=0.
        right = y[:, None] - edges[None, 1:]
        left = y[:, None] - edges[None, :-1]
        influence = (1 / right - 1 / left) / (4 * np.pi)
    else:
        influence = wake_matrix(y, np.full_like(y, height_m), edges, height_m)
    matrix = np.diag(2 / (chord * wing.section_slope_per_rad)) - influence
    rhs = np.full(panels, speed_m_s * alpha_rad)
    gamma = np.linalg.solve(matrix, rhs)
    w = influence @ gamma
    dy = np.diff(edges)
    cl = 2 * np.dot(gamma, dy) / (speed_m_s * wing.area_m2)
    cdi = -2 * np.dot(gamma * w, dy) / (speed_m_s ** 2 * wing.area_m2)
    return Solution(y, chord, dy, gamma, w, alpha_rad, float(cl), float(cdi),
                    float(np.max(np.abs(matrix @ gamma - rhs))))


def fixed_lift(wing, cl, height_m=None, panels=96):
    """Use linearity to obtain alpha and induced drag at prescribed total CL."""
    if not math.isfinite(cl) or cl <= 0:
        raise ValueError("Requested CL must be positive and finite")
    unit = solve(wing, math.radians(1), height_m, panels)
    alpha = unit.alpha_rad * cl / unit.cl
    return solve(wing, alpha, height_m, panels)
