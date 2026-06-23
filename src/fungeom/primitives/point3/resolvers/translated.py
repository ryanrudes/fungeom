"""A point displaced by a vector."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class TranslatedPoint3(Point3):
    """``point + offset`` — resolvable iff both are."""

    point: Point3
    offset: Vec3

    def _decide(self) -> Point3Decision:
        match self.point.decide(), self.offset.decide():
            case Resolvable(base), Resolvable(shift):
                return Resolvable(Point3Value(coord=base.coord + shift, frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
