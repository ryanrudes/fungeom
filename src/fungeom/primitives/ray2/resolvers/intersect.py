"""Where a 2D ray meets a 2D line (→ Point2) — the planar raycast; partial without a forward hit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.ray2.resolvers.base import Ray2


@dataclass(frozen=True, eq=False)
class Ray2LineIntersection(Point2):
    """The point where ``ray`` first meets ``line`` (→ ``Point2``).

    Solves ``t = (line.point − origin) · normal / (direction · normal)``. **Unresolvable**
    when the ray is parallel to the line (``direction · normal == 0``) or the hit is behind
    the origin (``t < 0`` — the ray points away from the line).
    """

    ray: Ray2
    line: Line2

    def _decide(self) -> Point2Decision:
        match self.ray.decide(), self.line.decide():
            case Resolvable(ray), Resolvable(line):
                normal = line.normal()
                denominator = float(np.dot(ray.direction, normal))
                if denominator == 0.0:
                    return Unresolvable("the ray is parallel to the line; there is no unique intersection")
                t = float(np.dot(line.point - ray.point, normal)) / denominator
                if t < 0.0:
                    return Unresolvable("the line is behind the ray's origin; the ray never reaches it")
                return Resolvable(Point2Value(coord=ray.point_at(t), frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
