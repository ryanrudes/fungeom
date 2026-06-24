"""A 2D line's representative point (→ Point2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


@dataclass(frozen=True, eq=False)
class Line2Origin(Point2):
    """``line``'s representative point — total."""

    line: Line2

    def _decide(self) -> Point2Decision:
        match self.line.decide():
            case Resolvable(line):
                return Resolvable(Point2Value(coord=line.point, frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
