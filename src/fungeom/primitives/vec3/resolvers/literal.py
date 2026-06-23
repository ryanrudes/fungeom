"""A resolver for an already-known vector."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.arrays import ArrayLike, freeze
from fungeom.core.resolvability import Resolvable
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class LiteralVec3(Vec3):
    """A vector that is already known — always resolvable."""

    value: Float3

    def __post_init__(self) -> None:
        value = as_vec3(self.value)
        freeze(value)
        object.__setattr__(self, "value", value)

    def _decide(self) -> Vec3Decision:
        return Resolvable(self.value)


def vec3_resolver(value: ArrayLike) -> Vec3:
    """Build a :class:`Vec3` from any array-like."""
    return LiteralVec3(value=as_vec3(value))
