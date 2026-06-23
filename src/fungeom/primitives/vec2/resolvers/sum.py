"""The sum of two 2D vectors."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class SumVec2(Vec2):
    """``a + b`` — resolvable iff both addends are."""

    a: Vec2
    b: Vec2

    def _decide(self) -> Vec2Decision:
        match self.a.decide(), self.b.decide():
            case Resolvable(va), Resolvable(vb):
                return Resolvable(va + vb)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
