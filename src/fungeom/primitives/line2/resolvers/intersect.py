"""The point where two 2D lines meet (→ Point2) — partial when they are parallel."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


def _cross(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


@dataclass(frozen=True, eq=False)
class Line2Intersect(Point2):
    """The point where ``first`` and ``second`` cross (→ ``Point2``; Unresolvable if parallel).

    Solves ``first.point + t · first.direction = second.point + s · second.direction``
    via the 2D cross product. **Unresolvable** when the directions are parallel
    (``first.direction × second.direction == 0`` — they never cross, or are collinear).
    """

    first: Line2
    second: Line2

    def _decide(self) -> Point2Decision:
        match self.first.decide(), self.second.decide():
            case Resolvable(a), Resolvable(b):
                da = (float(a.direction[0]), float(a.direction[1]))
                db = (float(b.direction[0]), float(b.direction[1]))
                denominator = _cross(da, db)
                if denominator == 0.0:
                    return Unresolvable("parallel lines do not meet in a point")
                offset = (float(b.point[0] - a.point[0]), float(b.point[1] - a.point[1]))
                t = _cross(offset, db) / denominator
                return Resolvable(Point2Value(coord=a.point_at(t), frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
