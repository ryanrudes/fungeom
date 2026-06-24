"""A segment with its endpoints swapped."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.segment.decidability import SegmentDecision
from fungeom.primitives.segment.resolvers.base import Segment
from fungeom.primitives.segment.value import SegmentValue


@dataclass(frozen=True, eq=False)
class SegmentReversed(Segment):
    """``segment`` with ``start`` and ``end`` swapped — total."""

    segment: Segment

    def _decide(self) -> SegmentDecision:
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(SegmentValue(start=segment.end, end=segment.start))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
