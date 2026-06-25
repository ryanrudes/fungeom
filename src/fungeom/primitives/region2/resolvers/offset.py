"""A region grown (≥0) or eroded (<0) by a distance — general, via GEOS buffering."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.shapely_bridge import from_shapely, to_shapely


@dataclass(frozen=True, eq=False)
class OffsetRegion2(Region2):
    """``region`` offset by ``distance`` — dilated (> 0) or eroded (< 0); erosion past extinction → empty.

    A general (any simple polygon, with holes) Minkowski offset via GEOS ``buffer`` (rounded
    joins); total given a resolvable region. The empty region offsets to itself.
    """

    region: Region2
    distance: float

    def _decide(self) -> Region2Decision:
        match self.region.decide():
            case Resolvable(region):
                if region.is_empty:
                    return Resolvable(region)
                return Resolvable(from_shapely(to_shapely(region).buffer(self.distance)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
