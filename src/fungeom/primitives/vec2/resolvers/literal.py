"""A resolver for an already-known 2D vector."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.arrays import freeze
from fungeom.core.resolvability import Resolvable
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2
from fungeom.primitives.vec2.value import Float2, as_vec2


@dataclass(frozen=True, eq=False)
class LiteralVec2(Vec2):
    """A 2D vector that is already known — always resolvable."""

    value: Float2

    def __post_init__(self) -> None:
        value = as_vec2(self.value)
        freeze(value)
        object.__setattr__(self, "value", value)

    def _decide(self) -> Vec2Decision:
        return Resolvable(self.value)


def vec2_resolver(value: Float2) -> Vec2:
    """Wrap a bare 2D vector value in a literal resolver."""
    return LiteralVec2(value=value)
