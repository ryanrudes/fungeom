"""The average of several 2D points."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


@dataclass(frozen=True, eq=False)
class Centroid2(Point2):
    """The centroid of the given points — resolvable iff every input is, never for none."""

    points: tuple[Point2, ...]

    def _decide(self) -> Point2Decision:
        if not self.points:
            return Unresolvable("centroid of no points is undefined")
        decided = gather(p.decide() for p in self.points)
        if isinstance(decided, Unresolvable):
            return decided
        mean = np.mean([p.coord for p in decided.value], axis=0)
        return Resolvable(Point2Value(coord=mean, frame=WORLD_FRAME2))
