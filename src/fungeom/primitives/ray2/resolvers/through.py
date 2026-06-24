"""A 2D ray from an origin and a direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.ray2.decidability import Ray2Decision
from fungeom.primitives.ray2.resolvers.base import Ray2
from fungeom.primitives.ray2.value import Ray2Value


@dataclass(frozen=True, eq=False)
class Ray2Through(Ray2):
    """The ray from ``anchor`` extending along ``axis``."""

    anchor: Point2
    axis: Direction2

    def _decide(self) -> Ray2Decision:
        match self.anchor.decide(), self.axis.decide():
            case Resolvable(origin), Resolvable(direction):
                return Resolvable(Ray2Value(point=origin.coord, direction=direction.vector))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
