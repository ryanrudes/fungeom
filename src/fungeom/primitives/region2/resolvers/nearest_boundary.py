"""The closest boundary point of a region to a query point (→ Point2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.region2.resolvers.base import Region2


@dataclass(frozen=True, eq=False)
class Region2NearestBoundaryPoint(Point2):
    """The point on ``region``'s boundary closest to ``point`` — Unresolvable for an empty region.

    The companion to :class:`Region2SignedDistance`: where on the support edge the margin is
    measured. Works whether ``point`` is inside or outside (it always lands on the boundary).
    """

    region: Region2
    point: Point2

    def _decide(self) -> Point2Decision:
        match self.region.decide(), self.point.decide():
            case (Resolvable(region), Resolvable(point)):
                if region.is_empty:
                    return Unresolvable("an empty region has no nearest boundary point")
                return Resolvable(Point2Value(coord=region.nearest_boundary_point(point.coord), frame=WORLD_FRAME2))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
