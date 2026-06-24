"""The dimensionless ratio of two durations — partial where the denominator is zero.

This resolves to a *scalar* (it is dimensionless), but it is built from durations
and so lives under ``duration``: ``duration`` already depends on ``scalar``, and
the reverse dependency would be a cycle. It mirrors ``QuotientScalar``.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class DurationRatio(Scalar):
    """``numerator / denominator`` as a dimensionless scalar.

    Unresolvable when the denominator resolves to a zero duration — a
    *value-dependent* partiality discovered only by deciding.
    """

    numerator: Duration
    denominator: Duration

    def _decide(self) -> ScalarDecision:
        match self.numerator.decide(), self.denominator.decide():
            case Resolvable(n), Resolvable(d):
                if d == 0.0:
                    return Unresolvable("ratio of a zero duration")
                return Resolvable(n / d)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
