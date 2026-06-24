"""A resolver for an already-known truth value, plus bool coercion."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.boolean.value import as_bool


@dataclass(frozen=True, eq=False)
class LiteralBool(Bool):
    """A truth value that is already known — always resolvable."""

    value: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", as_bool(self.value))

    def _decide(self) -> BoolDecision:
        return Resolvable(self.value)
