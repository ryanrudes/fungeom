"""A 2D direction as a (unit) vector (→ Vec2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class Direction2Vec2(Vec2):
    """``direction`` as a unit vector — total."""

    direction: Direction2

    def _decide(self) -> Vec2Decision:
        match self.direction.decide():
            case Resolvable(value):
                return Resolvable(value.vector)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
