"""The plane *value*: an oriented plane in 3D — a point on it plus a unit normal.

A :class:`PlaneValue` is an *oriented* plane: the normal has a meaningful direction
(an "outward" side), so a plane and its flip are distinct values. It is stored as a
representative ``point`` on the plane and a unit ``normal`` (normalized at
construction, like a :class:`~fungeom.values.Direction3Value`). The plane equation is
``normal · x = normal · point``; everything else (signed distance, projection, a
parallel offset) is derived from those two.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class PlaneValue:
    """An oriented plane: a world-frame ``point`` on it and a unit ``normal``.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for a tolerant
    comparison that treats two representative points of the same oriented plane as equal.
    """

    point: Float3
    normal: Float3

    def __post_init__(self) -> None:
        point = as_vec3(self.point)
        normal = as_vec3(self.normal)
        magnitude = float(np.linalg.norm(normal))
        if magnitude == 0.0:
            raise ValueError("a plane cannot have a zero normal")
        normal = normal / magnitude + 0.0  # canonicalize -0.0
        freeze(point)
        freeze(normal)
        object.__setattr__(self, "point", point)
        object.__setattr__(self, "normal", normal)

    def signed_distance(self, p: Float3) -> float:
        """Signed distance from ``p`` to the plane (positive on the ``normal`` side)."""
        return float(np.dot(self.normal, as_vec3(p) - self.point))

    def project(self, p: Float3) -> Float3:
        """The orthogonal projection of ``p`` onto the plane."""
        coord = as_vec3(p)
        return as_vec3(coord - self.signed_distance(coord) * self.normal)

    def offset(self, distance: float) -> PlaneValue:
        """A parallel plane shifted ``distance`` along the normal."""
        return PlaneValue(point=as_vec3(self.point + distance * self.normal), normal=self.normal)

    def flipped(self) -> PlaneValue:
        """The same plane with the opposite (negated) normal."""
        return PlaneValue(point=self.point, normal=as_vec3(-self.normal))

    def approx_equal(self, other: PlaneValue, atol: float = 1e-9) -> bool:
        """True if both are the same *oriented* plane (same normal and offset) within ``atol``."""
        return bool(
            np.allclose(self.normal, other.normal, atol=atol)
            and abs(float(np.dot(self.normal, self.point)) - float(np.dot(other.normal, other.point))) <= atol
        )

    def __repr__(self) -> str:
        px, py, pz = self.point
        nx, ny, nz = self.normal
        return f"PlaneValue(point=[{px:g}, {py:g}, {pz:g}], normal=[{nx:g}, {ny:g}, {nz:g}])"
