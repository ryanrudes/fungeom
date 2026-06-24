"""A segment from two endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.segment.decidability import SegmentDecision
from fungeom.primitives.segment.resolvers.base import Segment
from fungeom.primitives.segment.value import SegmentValue


@dataclass(frozen=True, eq=False)
class SegmentBetween(Segment):
    """The segment from ``a`` to ``b``."""

    a: Point3
    b: Point3

    def _decide(self) -> SegmentDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(start), Resolvable(end):
                return Resolvable(SegmentValue(start=start.coord, end=end.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
