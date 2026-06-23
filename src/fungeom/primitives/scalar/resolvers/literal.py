"""A resolver for an already-known scalar, plus float coercion."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.scalar.value import as_scalar


@dataclass(frozen=True, eq=False)
class LiteralScalar(Scalar):
    """A scalar that is already known — always resolvable."""

    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", as_scalar(self.value))

    def _decide(self) -> ScalarDecision:
        return Resolvable(self.value)


def as_scalar_resolver(value: float | Scalar) -> Scalar:
    """Lift a bare number into a literal resolver; pass resolvers through.

    This is the coercion that lets the fluent API accept plain floats while
    keeping every scalar a graph node underneath.
    """
    if isinstance(value, Scalar):
        return value
    return LiteralScalar(value=as_scalar(value))
