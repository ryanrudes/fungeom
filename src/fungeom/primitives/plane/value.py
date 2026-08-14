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
from fungeom.primitives.transform.value import RigidTransform
from fungeom.primitives.vec2.value import Float2, as_vec2
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

    def local_axes(self) -> tuple[Float3, Float3]:
        """A deterministic right-handed in-plane basis ``(x, y)`` (with ``x × y = normal``).

        The plane's intrinsic 2D chart. The gauge (rotation about the normal) is arbitrary
        but fixed by the normal alone — crossing with the coordinate axis least aligned with
        it — so :meth:`to_local` and :meth:`embed` are mutual inverses on the plane.

        **Memoized on first use**, the way a ``Resolver`` memoizes its decision and for the same
        reason: the chart is a pure function of an immutable normal, but it is asked for once per
        *point charted* — half a million times for one cloud over one take — so recomputing it is
        a per-point cost standing in for a constant. Lazily, not in ``__post_init__``: most planes
        are never charted at all, and two ``np.cross`` calls are not free either. The axes are
        handed out frozen, like every other array a value type exposes.
        """
        cached: tuple[Float3, Float3] | None = getattr(self, "_axes", None)
        if cached is None:
            helper = np.zeros(3)
            helper[int(np.argmin(np.abs(self.normal)))] = 1.0
            x = np.cross(self.normal, helper)
            x = x / float(np.linalg.norm(x))
            y = np.cross(self.normal, x)
            cached = (as_vec3(x), as_vec3(y))
            freeze(cached[0])
            freeze(cached[1])
            object.__setattr__(self, "_axes", cached)
        return cached

    def to_local(self, p: Float3) -> Float2:
        """The 2D coordinates of ``p`` in the plane's chart (orthogonally projected in-plane)."""
        x, y = self.local_axes()
        d = as_vec3(p) - self.point
        return as_vec2((float(np.dot(d, x)), float(np.dot(d, y))))

    def embed(self, uv: Float2) -> Float3:
        """The world point at chart coordinates ``uv`` — the inverse of :meth:`to_local` on the plane."""
        x, y = self.local_axes()
        u, v = as_vec2(uv)
        return as_vec3(self.point + u * x + v * y)

    def offset(self, distance: float) -> PlaneValue:
        """A parallel plane shifted ``distance`` along the normal."""
        return PlaneValue(point=as_vec3(self.point + distance * self.normal), normal=self.normal)

    def transformed_by(self, transform: RigidTransform) -> PlaneValue:
        """This plane moved by a rigid ``transform`` — the point is moved, the normal rotated."""
        return PlaneValue(point=transform.apply_point(self.point), normal=transform.apply_vector(self.normal))

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
