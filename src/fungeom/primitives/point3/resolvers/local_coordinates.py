"""A point's coordinates expressed in a given frame — the read-side inverse of ``in_frame``.

This is a ``Vec3`` (it resolves to the local coordinate triple), but it is built from a point
and a frame and so lives under ``point3``, exactly like :class:`DisplacementVec3`: ``point3``
already depends on ``vec3`` and ``frame``, and the reverse dependency would be a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class LocalCoordinates3(Vec3):
    """The coordinates of ``point`` re-expressed in ``frame`` — the inverse of ``Point3.in_frame``.

    Where ``in_frame`` *builds* a world-anchored point from a local coordinate vector in a frame,
    this *reads* that vector back. Resolvable iff the point is and ``frame`` is grounded — a
    detached frame resolves to :class:`~fungeom.Unresolvable`, so it never reaches ``to_frame``.
    """

    point: Point3
    frame: Frame

    def _decide(self) -> Vec3Decision:
        match self.point.decide(), self.frame.decide():
            case Resolvable(point), Resolvable(frame):
                # ``point`` is world-anchored and ``frame`` is grounded (same world root), so
                # ``to_frame`` re-expresses without raising; its ``coord`` is the local vector.
                return Resolvable(point.to_frame(frame).coord)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
