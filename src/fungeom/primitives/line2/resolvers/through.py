"""A 2D line from a point and a direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.line2.decidability import Line2Decision
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.line2.value import Line2Value
from fungeom.primitives.point2.resolvers.base import Point2


@dataclass(frozen=True, eq=False)
class Line2Through(Line2):
    """The line through ``anchor`` along ``axis``."""

    anchor: Point2
    axis: Direction2

    def _decide(self) -> Line2Decision:
        match self.anchor.decide(), self.axis.decide():
            case Resolvable(point), Resolvable(direction):
                return Resolvable(Line2Value(point=point.coord, direction=direction.vector))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
