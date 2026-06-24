"""A duration multiplied by a (deferred) scalar."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class ScaledDuration(Duration):
    """``duration * factor`` — resolvable iff both the duration and the factor are.

    This one resolver backs scaling (``*`` / :meth:`~Duration.scale`), scalar
    division (``/``, via a reciprocal factor), and negation (factor ``-1``).
    """

    duration: Duration
    factor: Scalar

    def _decide(self) -> DurationDecision:
        match self.duration.decide(), self.factor.decide():
            case Resolvable(duration), Resolvable(factor):
                return Resolvable(duration * factor)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
