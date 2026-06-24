"""A 2D direction transformed by a 2D transform — rotated, stays unit length (→ Direction2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class TransformedDirection2(Direction2):
    """``direction`` rotated by ``transform`` — total (a rigid rotation preserves unit length)."""

    transform: Transform2
    direction: Direction2

    def _decide(self) -> Direction2Decision:
        match self.transform.decide(), self.direction.decide():
            case Resolvable(transform), Resolvable(direction):
                return Resolvable(Direction2Value(vector=transform.apply_vector(direction.vector)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
