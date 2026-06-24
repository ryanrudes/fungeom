"""A 2D segment with its endpoints swapped."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.segment2.decidability import Segment2Decision
from fungeom.primitives.segment2.resolvers.base import Segment2
from fungeom.primitives.segment2.value import Segment2Value


@dataclass(frozen=True, eq=False)
class Segment2Reversed(Segment2):
    """``segment`` with ``start`` and ``end`` swapped — total."""

    segment: Segment2

    def _decide(self) -> Segment2Decision:
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(Segment2Value(start=segment.end, end=segment.start))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
