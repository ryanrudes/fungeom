"""A point moved by a rigid transform (a motion in the world frame)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class TransformedPoint3(Point3):
    """``transform`` applied to ``point`` as a rigid motion in the world frame.

    Resolvable iff both are: the point world-anchors, then the transform (rotation
    *and* translation) is applied to that world position.
    """

    point: Point3
    transform: Transform

    def _decide(self) -> Point3Decision:
        match self.point.decide(), self.transform.decide():
            case Resolvable(p), Resolvable(t):
                return Resolvable(Point3Value(coord=t.apply_point(p.coord), frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
