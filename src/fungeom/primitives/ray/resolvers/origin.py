"""A ray's origin (→ Point3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.ray.resolvers.base import Ray


@dataclass(frozen=True, eq=False)
class RayOrigin(Point3):
    """``ray``'s start point — total."""

    ray: Ray

    def _decide(self) -> Point3Decision:
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(Point3Value(coord=ray.point, frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
