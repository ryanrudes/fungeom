"""One scalar modulo another — partial where the modulus is zero."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class ModScalar(Scalar):
    """``value % modulus`` (result takes the modulus' sign).

    Unresolvable when ``modulus`` resolves to zero — a value-dependent partiality,
    the modular sibling of division by zero.
    """

    value: Scalar
    modulus: Scalar

    def _decide(self) -> ScalarDecision:
        match self.value.decide(), self.modulus.decide():
            case Resolvable(a), Resolvable(m):
                if m == 0.0:
                    return Unresolvable("modulo by zero")
                return Resolvable(a % m)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
