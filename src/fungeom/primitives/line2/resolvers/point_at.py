"""A point at a signed arc-length along a 2D line (→ Point2) — total."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


@dataclass(frozen=True, eq=False)
class Line2PointAt(Point2):
    """The point at signed arc-length ``distance`` along ``line`` from its origin — total."""

    line: Line2
    distance: float

    def _decide(self) -> Point2Decision:
        match self.line.decide():
            case Resolvable(line):
                return Resolvable(Point2Value(coord=line.point_at(self.distance), frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
