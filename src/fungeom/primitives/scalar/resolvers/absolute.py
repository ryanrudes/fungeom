"""The absolute value of a scalar."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class AbsScalar(Scalar):
    """``|value|`` — resolvable iff ``value`` is."""

    value: Scalar

    def _decide(self) -> ScalarDecision:
        decided = self.value.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(abs(decided.value))
