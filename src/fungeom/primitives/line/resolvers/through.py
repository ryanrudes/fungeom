"""A line from a point and a direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.line.decidability import LineDecision
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.line.value import LineValue
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class LineThrough(Line):
    """The line through ``anchor`` along ``axis``."""

    anchor: Point3
    axis: Direction3

    def _decide(self) -> LineDecision:
        match self.anchor.decide(), self.axis.decide():
            case Resolvable(point), Resolvable(direction):
                return Resolvable(LineValue(point=point.coord, direction=direction.vector))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
