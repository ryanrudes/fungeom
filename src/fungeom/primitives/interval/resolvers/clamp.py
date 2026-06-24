"""An instant clamped into an interval."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval


@dataclass(frozen=True, eq=False)
class IntervalClamp(Instant):
    """``instant`` clamped into ``interval`` (the nearest instant within ``[start, end]``)."""

    interval: Interval
    instant: Instant

    def _decide(self) -> InstantDecision:
        match self.interval.decide(), self.instant.decide():
            case Resolvable(span), Resolvable(t):
                return Resolvable(min(max(t, span.start), span.end))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
