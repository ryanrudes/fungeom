"""A point reflected through another point (central symmetry)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class ReflectedPoint3(Point3):
    """``point`` reflected through ``center`` — the position ``2·center − point``.

    Resolvable iff both are (the reflection of any point through any center is
    well-defined).
    """

    point: Point3
    center: Point3

    def _decide(self) -> Point3Decision:
        match self.point.decide(), self.center.decide():
            case Resolvable(p), Resolvable(c):
                return Resolvable(Point3Value(coord=2.0 * c.coord - p.coord, frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
