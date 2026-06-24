"""A 2D point displaced by a vector."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class TranslatedPoint2(Point2):
    """``point + offset`` — resolvable iff both are."""

    point: Point2
    offset: Vec2

    def _decide(self) -> Point2Decision:
        match self.point.decide(), self.offset.decide():
            case Resolvable(base), Resolvable(shift):
                return Resolvable(Point2Value(coord=base.coord + shift, frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
