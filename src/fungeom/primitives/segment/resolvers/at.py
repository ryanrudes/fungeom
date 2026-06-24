"""A point at a parameter along a segment (→ Point3) — partial outside [0, 1]."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.segment.resolvers.base import Segment


@dataclass(frozen=True, eq=False)
class SegmentAt(Point3):
    """The point at parameter ``t`` along ``segment`` (Unresolvable when ``t`` is outside ``[0, 1]``)."""

    segment: Segment
    t: float

    def _decide(self) -> Point3Decision:
        if not 0.0 <= self.t <= 1.0:
            return Unresolvable("a segment has no point at a parameter outside [0, 1]")
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(Point3Value(coord=segment.point_at(self.t), frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
