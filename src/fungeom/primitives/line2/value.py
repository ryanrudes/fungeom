"""The line2 *value*: an oriented line in 2D — a point on it plus a unit direction.

In 2D a line is a *hyperplane*: it has both a direction (along it) and a normal (across
it). A :class:`Line2Value` carries the unit ``direction`` and derives the left ``normal``
(a quarter turn counter-clockwise), so it offers both the line algebra (project,
distance) and the plane algebra (signed distance, a half-plane side). It is *oriented* —
a line and its reverse are distinct values (their normals point opposite ways).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec2.value import Float2, as_vec2


@dataclass(frozen=True, eq=False)
class Line2Value:
    """An oriented 2D line: a world-frame ``point`` on it and a unit ``direction`` along it.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for a tolerant,
    *oriented* comparison.
    """

    point: Float2
    direction: Float2

    def __post_init__(self) -> None:
        point = as_vec2(self.point)
        direction = as_vec2(self.direction)
        magnitude = float(np.linalg.norm(direction))
        if magnitude == 0.0:
            raise ValueError("a line cannot have a zero direction")
        direction = direction / magnitude + 0.0  # canonicalize -0.0
        freeze(point)
        freeze(direction)
        object.__setattr__(self, "point", point)
        object.__setattr__(self, "direction", direction)

    def normal(self) -> Float2:
        """The unit left normal — the direction turned a quarter turn counter-clockwise."""
        dx, dy = self.direction
        return as_vec2((-dy, dx))

    def parameter(self, p: Float2) -> float:
        """The signed arc-length of ``p``'s foot from ``point`` (``(p - point) · direction``)."""
        return float(np.dot(as_vec2(p) - self.point, self.direction))

    def project(self, p: Float2) -> Float2:
        """The orthogonal projection of ``p`` onto the line (its closest point)."""
        coord = as_vec2(p)
        return as_vec2(self.point + self.parameter(coord) * self.direction)

    def signed_distance(self, p: Float2) -> float:
        """The signed distance from ``p`` to the line (positive on the left-normal side)."""
        return float(np.dot(as_vec2(p) - self.point, self.normal()))

    def distance_to(self, p: Float2) -> float:
        """The unsigned perpendicular distance from ``p`` to the line."""
        return abs(self.signed_distance(p))

    def reversed(self) -> Line2Value:
        """The same line with the opposite direction (and so the opposite normal)."""
        return Line2Value(point=self.point, direction=as_vec2(-self.direction))

    def approx_equal(self, other: Line2Value, atol: float = 1e-9) -> bool:
        """True if both are the same *oriented* line (same direction and locus) within ``atol``."""
        return bool(np.allclose(self.direction, other.direction, atol=atol) and self.distance_to(other.point) <= atol)

    def __repr__(self) -> str:
        px, py = self.point
        dx, dy = self.direction
        return f"Line2Value(point=[{px:g}, {py:g}], direction=[{dx:g}, {dy:g}])"
