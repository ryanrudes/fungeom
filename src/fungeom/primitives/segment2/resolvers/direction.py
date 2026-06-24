"""A 2D segment's unit direction (→ Direction2) — partial when degenerate."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2Direction(Direction2):
    """The unit direction from ``segment``'s start to its end (Unresolvable if zero-length)."""

    segment: Segment2

    def _decide(self) -> Direction2Decision:
        match self.segment.decide():
            case Resolvable(segment):
                if segment.length() == 0.0:
                    return Unresolvable("a degenerate (zero-length) segment has no direction")
                return Resolvable(Direction2Value(vector=segment.displacement()))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
