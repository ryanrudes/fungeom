"""A 2D ray from an origin aimed at a target point — partial when they coincide."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.ray2.decidability import Ray2Decision
from fungeom.primitives.ray2.resolvers.base import Ray2
from fungeom.primitives.ray2.value import Ray2Value


@dataclass(frozen=True, eq=False)
class Ray2FromTo(Ray2):
    """The ray from ``source`` toward ``target`` (Unresolvable if they coincide)."""

    source: Point2
    target: Point2

    def _decide(self) -> Ray2Decision:
        decided = gather((self.source.decide(), self.target.decide()))
        if isinstance(decided, Unresolvable):
            return decided
        origin, aim = (point.coord for point in decided.value)
        direction = aim - origin
        if float(np.linalg.norm(direction)) == 0.0:
            return Unresolvable("a ray needs a target distinct from its origin")
        return Resolvable(Ray2Value(point=origin, direction=direction))
