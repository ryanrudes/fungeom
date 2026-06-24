"""The longer (more positive) of two durations."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration


@dataclass(frozen=True, eq=False)
class MaxDuration(Duration):
    """``max(a, b)`` — resolvable iff both are.

    Durations are signed seconds and so totally ordered; the maximum is the more
    positive (later-leaning) span.
    """

    a: Duration
    b: Duration

    def _decide(self) -> DurationDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(max(a, b))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
