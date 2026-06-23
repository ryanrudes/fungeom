"""The average of several points."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.frame import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class Centroid3(Point3):
    """The centroid of the given points.

    Resolvable only if every input is — and, for a geometric reason, never for
    an empty collection.
    """

    points: tuple[Point3, ...]

    def _decide(self) -> Point3Decision:
        if not self.points:
            return Unresolvable("centroid of no points is undefined")
        decided = gather(p.decide() for p in self.points)
        if isinstance(decided, Unresolvable):
            return decided
        mean = np.mean([p.coord for p in decided.value], axis=0)
        return Resolvable(Point3Value(coord=mean, frame=WORLD_FRAME))
