"""A scalar clamped to a ``[low, high]`` range."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class ClampScalar(Scalar):
    """``min(max(value, low), high)``.

    Unresolvable if the bounds are inverted (``low > high``), which has no
    sensible clamp; resolvable iff all three inputs are.
    """

    value: Scalar
    low: Scalar
    high: Scalar

    def _decide(self) -> ScalarDecision:
        decided = gather([self.value.decide(), self.low.decide(), self.high.decide()])
        if isinstance(decided, Unresolvable):
            return decided
        value, low, high = decided.value
        if low > high:
            return Unresolvable(f"clamp bounds are inverted (low {low} > high {high})")
        return Resolvable(min(max(value, low), high))
