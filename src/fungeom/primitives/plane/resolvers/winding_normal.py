"""A plane normal oriented by the winding of an ordered polygon (→ Direction3).

A plane's own normal has an arbitrary sign, but an ordered loop of points on (or near)
it picks a side: the one from which the loop runs counter-clockwise. Projecting the
points onto the plane and summing the signed-area vector about their centroid gives that
side directly (right-hand rule). A collinear or zero-area loop has no winding sense and
is ``Unresolvable``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class PlaneWindingNormal(Direction3):
    """The normal whose side ``points`` wind counter-clockwise around, on ``plane``."""

    plane: Plane
    points: tuple[Point3, ...]
    tolerance: float

    def _decide(self) -> Direction3Decision:
        if len(self.points) < 3:
            return Unresolvable("a winding normal needs at least three points")
        match self.plane.decide():
            case Resolvable(plane):
                decided = gather(tuple(point.decide() for point in self.points))
                if isinstance(decided, Unresolvable):
                    return decided
                projected = np.array([plane.project(point.coord) for point in decided.value])
                centroid = projected.mean(axis=0)
                spokes = projected - centroid
                area_vector = 0.5 * np.cross(spokes, np.roll(spokes, -1, axis=0)).sum(axis=0)
                max_radius = float(np.linalg.norm(spokes, axis=1).max())
                if float(np.linalg.norm(area_vector)) <= self.tolerance * max_radius**2:
                    return Unresolvable("the points enclose no area; their winding has no orientation")
                return Resolvable(Direction3Value(vector=area_vector))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
