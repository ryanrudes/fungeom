"""A coverage built from a collection of intervals."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.coverage.decidability import CoverageDecision
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue
from fungeom.primitives.interval.resolvers.base import Interval


@dataclass(frozen=True, eq=False)
class LiteralCoverage(Coverage):
    """The coverage spanning ``intervals`` (sorted and merged on resolution).

    Resolvable iff every interval is; the empty collection is the (resolvable)
    empty coverage.
    """

    intervals: tuple[Interval, ...]

    def _decide(self) -> CoverageDecision:
        decided = gather(span.decide() for span in self.intervals)
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(CoverageValue(intervals=tuple(decided.value)))
