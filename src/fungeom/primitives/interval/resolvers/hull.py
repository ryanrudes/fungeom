"""The convex hull of two intervals — the smallest span containing both."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue


@dataclass(frozen=True, eq=False)
class IntervalHull(Interval):
    """The smallest span containing both ``a`` and ``b`` (total — always resolvable)."""

    a: Interval
    b: Interval

    def _decide(self) -> IntervalDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(IntervalValue(start=min(a.start, b.start), end=max(a.end, b.end)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
