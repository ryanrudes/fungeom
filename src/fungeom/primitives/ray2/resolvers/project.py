"""Closest point of a 2D ray to a point (→ Point2), clamped behind the origin."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.ray2.resolvers.base import Ray2


@dataclass(frozen=True, eq=False)
class Ray2Project(Point2):
    """``point`` projected onto ``ray`` — the origin if it lies behind. Total."""

    ray: Ray2
    point: Point2

    def _decide(self) -> Point2Decision:
        match self.ray.decide(), self.point.decide():
            case Resolvable(ray), Resolvable(point):
                return Resolvable(Point2Value(coord=ray.project(point.coord), frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
