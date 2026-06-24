"""A 2D segment's endpoints (→ Point2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2Start(Point2):
    """``segment``'s start endpoint — total."""

    segment: Segment2

    def _decide(self) -> Point2Decision:
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(Point2Value(coord=segment.start, frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class Segment2End(Point2):
    """``segment``'s end endpoint — total."""

    segment: Segment2

    def _decide(self) -> Point2Decision:
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(Point2Value(coord=segment.end, frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
