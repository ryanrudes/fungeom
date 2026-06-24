"""The absolute value of a duration."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration


@dataclass(frozen=True, eq=False)
class AbsDuration(Duration):
    """``|value|`` — resolvable iff ``value`` is."""

    value: Duration

    def _decide(self) -> DurationDecision:
        decided = self.value.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(abs(decided.value))
