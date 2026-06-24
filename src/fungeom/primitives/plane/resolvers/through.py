"""A plane from a point and a normal direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class PlaneThrough(Plane):
    """The plane through ``anchor`` with normal ``axis``."""

    anchor: Point3
    axis: Direction3

    def _decide(self) -> PlaneDecision:
        match self.anchor.decide(), self.axis.decide():
            case Resolvable(point), Resolvable(normal):
                return Resolvable(PlaneValue(point=point.coord, normal=normal.vector))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
