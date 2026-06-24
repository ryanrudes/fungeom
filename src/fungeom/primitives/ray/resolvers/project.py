"""Closest point of a ray to a point (→ Point3), clamped behind the origin."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.ray.resolvers.base import Ray


@dataclass(frozen=True, eq=False)
class RayProject(Point3):
    """``point`` projected onto ``ray`` — the origin if it lies behind. Total."""

    ray: Ray
    point: Point3

    def _decide(self) -> Point3Decision:
        match self.ray.decide(), self.point.decide():
            case Resolvable(ray), Resolvable(point):
                return Resolvable(Point3Value(coord=ray.project(point.coord), frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
