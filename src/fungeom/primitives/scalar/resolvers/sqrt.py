"""The square root of a scalar — partial for negatives."""

from __future__ import annotations

import math
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class SqrtScalar(Scalar):
    """``√value`` — Unresolvable when ``value`` resolves to a negative number."""

    value: Scalar

    def _decide(self) -> ScalarDecision:
        decided = self.value.decide()
        if isinstance(decided, Unresolvable):
            return decided
        if decided.value < 0.0:
            return Unresolvable("square root of a negative number")
        return Resolvable(math.sqrt(decided.value))
