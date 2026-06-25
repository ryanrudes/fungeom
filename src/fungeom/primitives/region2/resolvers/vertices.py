"""A region's boundary vertices, keyed by position (→ Point2Bundle)."""

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
class Region2Vertices(Point2Bundle):
    """The boundary vertices of ``region``, keyed ``0..N-1`` in ring order (an empty region → empty cloud)."""

    region: Region2

    def _decide(self) -> BundleDecision[Point2Value]:
        match self.region.decide():
            case Resolvable(region):
                coords = [vertex for ring in region.rings for vertex in ring]
                members: dict[Hashable, Point2Value] = {
                    i: Point2Value(coord=coord, frame=WORLD_FRAME2) for i, coord in enumerate(coords)
                }
                return Resolvable(BundleValue(roster=tuple(range(len(coords))), members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
