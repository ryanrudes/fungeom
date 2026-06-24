"""Distance from a point to a ray (→ Scalar), to the origin if behind."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.ray.resolvers.base import Ray
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class RayDistanceTo(Scalar):
    """The distance from ``point`` to ``ray`` — total (non-negative)."""

    ray: Ray
    point: Point3

    def _decide(self) -> ScalarDecision:
        match self.ray.decide(), self.point.decide():
            case Resolvable(ray), Resolvable(point):
                return Resolvable(ray.distance_to(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
