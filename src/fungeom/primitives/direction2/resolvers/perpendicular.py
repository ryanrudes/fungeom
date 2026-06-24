"""The left perpendicular of a 2D direction — a quarter turn counter-clockwise."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2


@dataclass(frozen=True, eq=False)
class PerpendicularDirection2(Direction2):
    """``direction`` turned a quarter turn counter-clockwise — total (2D has a unique perpendicular)."""

    direction: Direction2

    def _decide(self) -> Direction2Decision:
        match self.direction.decide():
            case Resolvable(value):
                return Resolvable(value.perpendicular())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
