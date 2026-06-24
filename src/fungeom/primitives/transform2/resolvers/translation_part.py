"""A 2D transform's translation component (→ Vec2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class TranslationPart2(Vec2):
    """``transform``'s translation component, as a vector — total."""

    transform: Transform2

    def _decide(self) -> Vec2Decision:
        match self.transform.decide():
            case Resolvable(transform):
                return Resolvable(transform.translation)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
