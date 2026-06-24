"""A 2D point moved by a rigid transform (a motion in the world frame)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class TransformedPoint2(Point2):
    """``transform`` applied to ``point`` as a rigid motion in the world frame — resolvable iff both are."""

    point: Point2
    transform: Transform2

    def _decide(self) -> Point2Decision:
        match self.point.decide(), self.transform.decide():
            case Resolvable(p), Resolvable(t):
                return Resolvable(Point2Value(coord=t.apply_point(p.coord), frame=WORLD_FRAME2))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
