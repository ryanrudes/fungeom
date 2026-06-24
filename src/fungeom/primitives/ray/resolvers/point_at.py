"""A point a given distance along a ray (→ Point3) — partial for a negative distance."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.ray.resolvers.base import Ray


@dataclass(frozen=True, eq=False)
class RayPointAt(Point3):
    """The point ``distance`` along ``ray`` (Unresolvable when ``distance`` is negative — off the half-line)."""

    ray: Ray
    distance: float

    def _decide(self) -> Point3Decision:
        if self.distance < 0.0:
            return Unresolvable("a ray has no point at a negative distance (that is behind the origin)")
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(Point3Value(coord=ray.point_at(self.distance), frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
