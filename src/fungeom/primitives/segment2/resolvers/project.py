"""Closest point of a 2D segment to a point (→ Point2), clamped to the endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2Project(Point2):
    """``point`` projected onto ``segment`` — clamped to the endpoints. Total."""

    segment: Segment2
    point: Point2

    def _decide(self) -> Point2Decision:
        match self.segment.decide(), self.point.decide():
            case Resolvable(segment), Resolvable(point):
                return Resolvable(Point2Value(coord=segment.project(point.coord), frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
