"""Orthogonal projection of a point onto a line (→ Point3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class LineProject(Point3):
    """``point`` projected orthogonally onto ``line`` — total (a foot always exists)."""

    line: Line
    point: Point3

    def _decide(self) -> Point3Decision:
        match self.line.decide(), self.point.decide():
            case Resolvable(line), Resolvable(point):
                return Resolvable(Point3Value(coord=line.project(point.coord), frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
