"""The opposite of a 2D direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2


@dataclass(frozen=True, eq=False)
class ReversedDirection2(Direction2):
    """``direction`` reversed — total."""

    direction: Direction2

    def _decide(self) -> Direction2Decision:
        match self.direction.decide():
            case Resolvable(value):
                return Resolvable(value.reversed())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
