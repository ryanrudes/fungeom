"""The overlap of two intervals — partial when they are disjoint."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue


@dataclass(frozen=True, eq=False)
class IntervalIntersection(Interval):
    """The closed overlap ``a ∩ b``.

    Unresolvable when the two spans are disjoint (no overlap, not even a shared
    endpoint) — there is genuinely no interval to return. Spans that touch at a
    single instant intersect in that degenerate point.
    """

    a: Interval
    b: Interval

    def _decide(self) -> IntervalDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                low = max(a.start, b.start)
                high = min(a.end, b.end)
                if low > high:
                    return Unresolvable("intervals are disjoint")
                return Resolvable(IntervalValue(start=low, end=high))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
