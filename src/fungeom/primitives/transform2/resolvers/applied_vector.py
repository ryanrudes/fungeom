"""A 2D vector transformed by a 2D transform — rotated only (→ Vec2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class TransformedVec2(Vec2):
    """``vector`` rotated by ``transform`` (no translation) — total in both inputs."""

    transform: Transform2
    vector: Vec2

    def _decide(self) -> Vec2Decision:
        match self.transform.decide(), self.vector.decide():
            case Resolvable(transform), Resolvable(vector):
                return Resolvable(transform.apply_vector(vector))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
