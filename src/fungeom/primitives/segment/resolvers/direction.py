"""A segment's unit direction (→ Direction3) — partial when degenerate."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.segment.resolvers.base import Segment


@dataclass(frozen=True, eq=False)
class SegmentDirection(Direction3):
    """The unit direction from ``segment``'s start to its end (Unresolvable if zero-length)."""

    segment: Segment

    def _decide(self) -> Direction3Decision:
        match self.segment.decide():
            case Resolvable(segment):
                if segment.length() == 0.0:
                    return Unresolvable("a degenerate (zero-length) segment has no direction")
                return Resolvable(Direction3Value(vector=segment.displacement()))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
