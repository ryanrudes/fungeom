"""The vector spanning two points.

This is a ``Vec3`` (it resolves to a vector), but it is built from points
and so lives under ``point3``: ``point3`` already depends on ``vec3``, and the
reverse dependency would be a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class DisplacementVec3(Vec3):
    """The world-frame vector from ``start`` to ``end``.

    A vector whose resolvability is *not* trivial: it inherits the resolvability
    of the two points it spans.
    """

    start: Point3
    end: Point3

    def _decide(self) -> Vec3Decision:
        match self.start.decide(), self.end.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(b.coord - a.coord)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
