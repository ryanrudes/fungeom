"""The 2D vector spanning two points (lives under point2; point2 depends on vec2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class DisplacementVec2(Vec2):
    """The world-frame vector from ``start`` to ``end`` — inherits both points' resolvability."""

    start: Point2
    end: Point2

    def _decide(self) -> Vec2Decision:
        match self.start.decide(), self.end.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(b.coord - a.coord)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
