"""Round a scalar to the nearest integer."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class RoundScalar(Scalar):
    """``value`` rounded to the nearest integer (ties to even, as a float); resolvable iff ``value`` is."""

    value: Scalar

    def _decide(self) -> ScalarDecision:
        decided = self.value.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(float(round(decided.value)))
