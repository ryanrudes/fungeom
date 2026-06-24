"""The sum of two durations."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration


@dataclass(frozen=True, eq=False)
class SumDuration(Duration):
    """``a + b`` — resolvable iff both addends are.

    Subtraction is the same node with ``b`` negated, so this one resolver backs
    both ``+`` and ``-``.
    """

    a: Duration
    b: Duration

    def _decide(self) -> DurationDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a + b)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
