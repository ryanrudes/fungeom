"""An interval built from its two endpoints — partial when end precedes start."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue


@dataclass(frozen=True, eq=False)
class BetweenInterval(Interval):
    """The span ``[start, end]``.

    Unresolvable when ``end`` resolves to before ``start`` — a value-dependent
    partiality (the order-structured analog of ``clamp`` with ``low > high``).
    """

    start_at: Instant
    end_at: Instant

    def _decide(self) -> IntervalDecision:
        match self.start_at.decide(), self.end_at.decide():
            case Resolvable(start), Resolvable(end):
                if end < start:
                    return Unresolvable(f"interval start ({start:g}) is after end ({end:g})")
                return Resolvable(IntervalValue(start=start, end=end))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
