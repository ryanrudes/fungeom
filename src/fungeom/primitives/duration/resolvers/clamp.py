"""A duration clamped to a ``[low, high]`` range."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration


@dataclass(frozen=True, eq=False)
class ClampDuration(Duration):
    """``min(max(value, low), high)``.

    Unresolvable if the bounds are inverted (``low > high``), which has no
    sensible clamp; resolvable iff all three inputs are.
    """

    value: Duration
    low: Duration
    high: Duration

    def _decide(self) -> DurationDecision:
        decided = gather([self.value.decide(), self.low.decide(), self.high.decide()])
        if isinstance(decided, Unresolvable):
            return decided
        value, low, high = decided.value
        if low > high:
            return Unresolvable(f"clamp bounds are inverted (low {low}s > high {high}s)")
        return Resolvable(min(max(value, low), high))
