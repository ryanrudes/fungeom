"""A region's axis-aligned bounding box, as min/max corners (→ Point2Bundle)."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.point2 import Point2Bundle
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.region2.resolvers.base import Region2


@dataclass(frozen=True, eq=False)
class Region2Bounds(Point2Bundle):
    """The region's axis-aligned bounding box as a ``{'min', 'max'}`` cloud — Unresolvable if empty."""

    region: Region2

    def _decide(self) -> BundleDecision[Point2Value]:
        match self.region.decide():
            case Resolvable(region):
                if region.is_empty:
                    return Unresolvable("an empty region has no bounding box")
                low, high = region.bounds()
                members: dict[Hashable, Point2Value] = {
                    "min": Point2Value(coord=low, frame=WORLD_FRAME2),
                    "max": Point2Value(coord=high, frame=WORLD_FRAME2),
                }
                return Resolvable(BundleValue(roster=("min", "max"), members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
