"""Orthogonal projection of a point onto a 2D line (→ Point2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


@dataclass(frozen=True, eq=False)
class Line2Project(Point2):
    """``point`` projected orthogonally onto ``line`` — total (a foot always exists)."""

    line: Line2
    point: Point2

    def _decide(self) -> Point2Decision:
        match self.line.decide(), self.point.decide():
            case Resolvable(line), Resolvable(point):
                return Resolvable(Point2Value(coord=line.project(point.coord), frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
