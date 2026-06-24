"""The ray2 *value*: a half-line in 2D — an origin plus a unit direction.

The planar sibling of :class:`~fungeom.values.RayValue`: it starts at ``point`` (the
origin — a meaningful endpoint) and extends in ``direction`` for non-negative parameters
only. Projection clamps to that range, which is what distinguishes a ray from a line.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec2.value import Float2, as_vec2


@dataclass(frozen=True, eq=False)
class Ray2Value:
    """A 2D half-line: a world-frame ``point`` (the origin) and a unit ``direction``.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for a tolerant
    comparison (both the origin and the direction must agree — a ray's origin matters).
    """

    point: Float2
    direction: Float2

    def __post_init__(self) -> None:
        point = as_vec2(self.point)
        direction = as_vec2(self.direction)
        magnitude = float(np.linalg.norm(direction))
        if magnitude == 0.0:
            raise ValueError("a ray cannot have a zero direction")
        direction = direction / magnitude + 0.0  # canonicalize -0.0
        freeze(point)
        freeze(direction)
        object.__setattr__(self, "point", point)
        object.__setattr__(self, "direction", direction)

    def parameter(self, p: Float2) -> float:
        """The signed projection of ``p`` onto the ray's line (negative = behind the origin)."""
        return float(np.dot(as_vec2(p) - self.point, self.direction))

    def project(self, p: Float2) -> Float2:
        """The closest point of the ray to ``p`` — clamped to the origin when ``p`` is behind it."""
        t = max(0.0, self.parameter(p))
        return as_vec2(self.point + t * self.direction)

    def distance_to(self, p: Float2) -> float:
        """The distance from ``p`` to the ray (to the origin if ``p`` is behind it)."""
        coord = as_vec2(p)
        return float(np.linalg.norm(coord - self.project(coord)))

    def point_at(self, distance: float) -> Float2:
        """The point ``distance`` along the ray from the origin (caller ensures ``distance ≥ 0``)."""
        return as_vec2(self.point + distance * self.direction)

    def reversed(self) -> Ray2Value:
        """The opposite half-line from the same origin (the direction negated)."""
        return Ray2Value(point=self.point, direction=as_vec2(-self.direction))

    def approx_equal(self, other: Ray2Value, atol: float = 1e-9) -> bool:
        """True if both rays share an origin and a direction within ``atol``."""
        return bool(
            np.allclose(self.point, other.point, atol=atol) and np.allclose(self.direction, other.direction, atol=atol)
        )

    def __repr__(self) -> str:
        px, py = self.point
        dx, dy = self.direction
        return f"Ray2Value(origin=[{px:g}, {py:g}], direction=[{dx:g}, {dy:g}])"
