"""A ray from an origin aimed at a target point — partial when they coincide."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.ray.decidability import RayDecision
from fungeom.primitives.ray.resolvers.base import Ray
from fungeom.primitives.ray.value import RayValue


@dataclass(frozen=True, eq=False)
class RayFromTo(Ray):
    """The ray from ``source`` toward ``target`` (Unresolvable if they coincide)."""

    source: Point3
    target: Point3

    def _decide(self) -> RayDecision:
        decided = gather((self.source.decide(), self.target.decide()))
        if isinstance(decided, Unresolvable):
            return decided
        origin, aim = (point.coord for point in decided.value)
        direction = aim - origin
        if float(np.linalg.norm(direction)) == 0.0:
            return Unresolvable("a ray needs a target distinct from its origin")
        return Resolvable(RayValue(point=origin, direction=direction))
