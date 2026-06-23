"""Linear interpolation between two 2D vectors."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class LerpVec2(Vec2):
    """``(1 - t) * a + t * b`` — resolvable iff both vectors and ``t`` are."""

    a: Vec2
    b: Vec2
    t: Scalar

    def _decide(self) -> Vec2Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(a), Resolvable(b), Resolvable(t):
                return Resolvable(a * (1.0 - t) + b * t)
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
