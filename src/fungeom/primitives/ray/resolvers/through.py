"""A ray from an origin and a direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.ray.decidability import RayDecision
from fungeom.primitives.ray.resolvers.base import Ray
from fungeom.primitives.ray.value import RayValue


@dataclass(frozen=True, eq=False)
class RayThrough(Ray):
    """The ray from ``anchor`` extending along ``axis``."""

    anchor: Point3
    axis: Direction3

    def _decide(self) -> RayDecision:
        match self.anchor.decide(), self.axis.decide():
            case Resolvable(origin), Resolvable(direction):
                return Resolvable(RayValue(point=origin.coord, direction=direction.vector))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
