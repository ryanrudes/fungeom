"""A region's area-weighted centroid (→ Point2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.region2.resolvers.base import Region2


@dataclass(frozen=True, eq=False)
class Region2Centroid(Point2):
    """The area-weighted centroid of ``region`` — Unresolvable for an empty / zero-area region."""

    region: Region2

    def _decide(self) -> Point2Decision:
        match self.region.decide():
            case Resolvable(region):
                if region.area() == 0.0:
                    return Unresolvable("the centroid of an empty region is undefined")
                return Resolvable(Point2Value(coord=region.centroid(), frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
