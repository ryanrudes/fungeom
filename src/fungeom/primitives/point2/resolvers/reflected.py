"""A 2D point reflected through another point (central symmetry)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


@dataclass(frozen=True, eq=False)
class ReflectedPoint2(Point2):
    """``point`` reflected through ``center`` — the position ``2·center − point``. Resolvable iff both are."""

    point: Point2
    center: Point2

    def _decide(self) -> Point2Decision:
        match self.point.decide(), self.center.decide():
            case Resolvable(p), Resolvable(c):
                return Resolvable(Point2Value(coord=2.0 * c.coord - p.coord, frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
