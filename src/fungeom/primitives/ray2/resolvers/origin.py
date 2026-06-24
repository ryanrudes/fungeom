"""A 2D ray's origin (→ Point2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.ray2.resolvers.base import Ray2


@dataclass(frozen=True, eq=False)
class Ray2Origin(Point2):
    """``ray``'s start point — total."""

    ray: Ray2

    def _decide(self) -> Point2Decision:
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(Point2Value(coord=ray.point, frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
