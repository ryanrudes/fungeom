"""The sign of a scalar: -1, 0, or 1."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class SignScalar(Scalar):
    """``sign(value)`` — ``-1.0``, ``0.0``, or ``1.0``; resolvable iff ``value`` is."""

    value: Scalar

    def _decide(self) -> ScalarDecision:
        decided = self.value.decide()
        if isinstance(decided, Unresolvable):
            return decided
        x = decided.value
        return Resolvable(float((x > 0.0) - (x < 0.0)))
