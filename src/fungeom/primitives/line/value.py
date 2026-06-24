"""The line *value*: an oriented line in 3D — a point on it plus a unit direction.

A :class:`LineValue` is an *oriented* line: the direction has a meaningful sense (a
"forward"), so a line and its reverse are distinct values — the orientation is what a
line-fit tangent carries. It is stored as a representative ``point`` on the line and a
unit ``direction`` (normalized at construction, like a
:class:`~fungeom.values.Direction3Value`). Projection, distance and the line parameter
are all derived from those two.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class LineValue:
    """An oriented line: a world-frame ``point`` on it and a unit ``direction``.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for a tolerant
    comparison that treats two representative points of the same oriented line as equal.
    """

    point: Float3
    direction: Float3

    def __post_init__(self) -> None:
        point = as_vec3(self.point)
        direction = as_vec3(self.direction)
        magnitude = float(np.linalg.norm(direction))
        if magnitude == 0.0:
            raise ValueError("a line cannot have a zero direction")
        direction = direction / magnitude + 0.0  # canonicalize -0.0
        freeze(point)
        freeze(direction)
        object.__setattr__(self, "point", point)
        object.__setattr__(self, "direction", direction)

    def parameter(self, p: Float3) -> float:
        """The signed arc-length of ``p``'s foot from ``point`` (``(p - point) · direction``)."""
        return float(np.dot(as_vec3(p) - self.point, self.direction))

    def project(self, p: Float3) -> Float3:
        """The orthogonal projection of ``p`` onto the line (its closest point)."""
        coord = as_vec3(p)
        return as_vec3(self.point + self.parameter(coord) * self.direction)

    def distance_to(self, p: Float3) -> float:
        """The perpendicular distance from ``p`` to the line."""
        coord = as_vec3(p)
        return float(np.linalg.norm(coord - self.project(coord)))

    def reversed(self) -> LineValue:
        """The same line with the opposite (negated) direction."""
        return LineValue(point=self.point, direction=as_vec3(-self.direction))

    def approx_equal(self, other: LineValue, atol: float = 1e-9) -> bool:
        """True if both are the same *oriented* line (same direction and locus) within ``atol``."""
        return bool(np.allclose(self.direction, other.direction, atol=atol) and self.distance_to(other.point) <= atol)

    def __repr__(self) -> str:
        px, py, pz = self.point
        dx, dy, dz = self.direction
        return f"LineValue(point=[{px:g}, {py:g}, {pz:g}], direction=[{dx:g}, {dy:g}, {dz:g}])"
