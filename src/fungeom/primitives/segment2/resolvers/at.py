"""A point at a parameter along a 2D segment (→ Point2) — partial outside [0, 1]."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2At(Point2):
    """The point at parameter ``t`` along ``segment`` (Unresolvable when ``t`` is outside ``[0, 1]``)."""

    segment: Segment2
    t: float

    def _decide(self) -> Point2Decision:
        if not 0.0 <= self.t <= 1.0:
            return Unresolvable("a segment has no point at a parameter outside [0, 1]")
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(Point2Value(coord=segment.point_at(self.t), frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
