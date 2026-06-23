"""The quotient of two scalars — partial where the denominator is zero."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class QuotientScalar(Scalar):
    """``numerator / denominator``.

    Unresolvable when the denominator resolves to zero — a *value-dependent*
    partiality (the scalar analog of the centroid of no points), discovered only
    by deciding.
    """

    numerator: Scalar
    denominator: Scalar

    def _decide(self) -> ScalarDecision:
        match self.numerator.decide(), self.denominator.decide():
            case Resolvable(n), Resolvable(d):
                if d == 0.0:
                    return Unresolvable("division by zero")
                return Resolvable(n / d)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
