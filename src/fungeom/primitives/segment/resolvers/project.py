"""Closest point of a segment to a point (→ Point3), clamped to the endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.segment.resolvers.base import Segment


@dataclass(frozen=True, eq=False)
class SegmentProject(Point3):
    """``point`` projected onto ``segment`` — clamped to the endpoints. Total."""

    segment: Segment
    point: Point3

    def _decide(self) -> Point3Decision:
        match self.segment.decide(), self.point.decide():
            case Resolvable(segment), Resolvable(point):
                return Resolvable(Point3Value(coord=segment.project(point.coord), frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
