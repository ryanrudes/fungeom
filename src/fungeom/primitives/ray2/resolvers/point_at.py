"""A point a given distance along a 2D ray (→ Point2) — partial for a negative distance."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.ray2.resolvers.base import Ray2


@dataclass(frozen=True, eq=False)
class Ray2PointAt(Point2):
    """The point ``distance`` along ``ray`` (Unresolvable when ``distance`` is negative — off the half-line)."""

    ray: Ray2
    distance: float

    def _decide(self) -> Point2Decision:
        if self.distance < 0.0:
            return Unresolvable("a ray has no point at a negative distance (that is behind the origin)")
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(Point2Value(coord=ray.point_at(self.distance), frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
