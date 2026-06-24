"""Orthogonal projection of a point onto a plane (→ Point3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class PlaneProject(Point3):
    """``point`` projected orthogonally onto ``plane`` — total (a foot always exists)."""

    plane: Plane
    point: Point3

    def _decide(self) -> Point3Decision:
        match self.plane.decide(), self.point.decide():
            case Resolvable(plane), Resolvable(point):
                return Resolvable(Point3Value(coord=plane.project(point.coord), frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
