"""The ray *value*: a half-line in 3D — an origin plus a unit direction.

A :class:`RayValue` is an *oriented half-line*: it starts at ``point`` (the origin —
a meaningful endpoint, unlike a line's arbitrary representative) and extends in
``direction`` for non-negative parameters only. The origin and the direction are both
significant, so two rays are equal only when both agree. Projection clamps to the
non-negative parameter range, which is exactly what distinguishes a ray from a line.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class RayValue:
    """A half-line: a world-frame ``point`` (the origin) and a unit ``direction``.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for a tolerant
    comparison (both the origin and the direction must agree — a ray's origin matters).
    """

    point: Float3
    direction: Float3

    def __post_init__(self) -> None:
        point = as_vec3(self.point)
        direction = as_vec3(self.direction)
        magnitude = float(np.linalg.norm(direction))
        if magnitude == 0.0:
            raise ValueError("a ray cannot have a zero direction")
        direction = direction / magnitude + 0.0  # canonicalize -0.0
        freeze(point)
        freeze(direction)
        object.__setattr__(self, "point", point)
        object.__setattr__(self, "direction", direction)

    def parameter(self, p: Float3) -> float:
        """The signed projection of ``p`` onto the ray's line (negative = behind the origin)."""
        return float(np.dot(as_vec3(p) - self.point, self.direction))

    def project(self, p: Float3) -> Float3:
        """The closest point of the ray to ``p`` — clamped to the origin when ``p`` is behind it."""
        t = max(0.0, self.parameter(p))
        return as_vec3(self.point + t * self.direction)

    def distance_to(self, p: Float3) -> float:
        """The distance from ``p`` to the ray (to the origin if ``p`` is behind it)."""
        coord = as_vec3(p)
        return float(np.linalg.norm(coord - self.project(coord)))

    def point_at(self, distance: float) -> Float3:
        """The point ``distance`` along the ray from the origin (caller ensures ``distance ≥ 0``)."""
        return as_vec3(self.point + distance * self.direction)

    def reversed(self) -> RayValue:
        """The opposite half-line from the same origin (the direction negated)."""
        return RayValue(point=self.point, direction=as_vec3(-self.direction))

    def approx_equal(self, other: RayValue, atol: float = 1e-9) -> bool:
        """True if both rays share an origin and a direction within ``atol``."""
        return bool(
            np.allclose(self.point, other.point, atol=atol) and np.allclose(self.direction, other.direction, atol=atol)
        )

    def __repr__(self) -> str:
        px, py, pz = self.point
        dx, dy, dz = self.direction
        return f"RayValue(origin=[{px:g}, {py:g}, {pz:g}], direction=[{dx:g}, {dy:g}, {dz:g}])"
