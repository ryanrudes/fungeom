"""The point of a region closest to a query point (→ Point2) — clamp-into-region."""

from __future__ import annotations

from dataclasses import dataclass

from shapely import Point as ShapelyPoint
from shapely.ops import nearest_points

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.shapely_bridge import to_shapely
from fungeom.primitives.vec2.value import as_vec2


@dataclass(frozen=True, eq=False)
class Region2ClosestPoint(Point2):
    """The point of ``region`` closest to ``point`` — the query itself if inside, else the nearest
    boundary point. The clamp-into-region op (unlike :class:`Region2NearestBoundaryPoint`, an
    interior query is returned unchanged). Unresolvable for an empty region.
    """

    region: Region2
    point: Point2

    def _decide(self) -> Point2Decision:
        match self.region.decide(), self.point.decide():
            case (Resolvable(region), Resolvable(point)):
                if region.is_empty:
                    return Unresolvable("an empty region has no closest point")
                nearest = nearest_points(to_shapely(region), ShapelyPoint(point.coord))[0]
                return Resolvable(Point2Value(coord=as_vec2([nearest.x, nearest.y]), frame=WORLD_FRAME2))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
