"""Distance from a point to a 2D ray (→ Scalar), to the origin if behind."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.ray2.resolvers.base import Ray2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Ray2DistanceTo(Scalar):
    """The distance from ``point`` to ``ray`` — total (non-negative)."""

    ray: Ray2
    point: Point2

    def _decide(self) -> ScalarDecision:
        match self.ray.decide(), self.point.decide():
            case Resolvable(ray), Resolvable(point):
                return Resolvable(ray.distance_to(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
