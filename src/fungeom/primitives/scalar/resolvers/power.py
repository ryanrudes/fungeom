"""One scalar raised to another — partial where the result leaves the reals."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class PowerScalar(Scalar):
    """``base ** exponent``.

    Unresolvable where the real result is undefined: zero to a negative power, or
    a negative base raised to a fractional exponent (a complex result).
    """

    base: Scalar
    exponent: Scalar

    def _decide(self) -> ScalarDecision:
        match self.base.decide(), self.exponent.decide():
            case Resolvable(base), Resolvable(exponent):
                try:
                    result = base**exponent
                except ZeroDivisionError:
                    return Unresolvable("zero raised to a negative power")
                if isinstance(result, complex):
                    return Unresolvable("negative base raised to a fractional power")
                return Resolvable(result)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
