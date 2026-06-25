"""Evenly-spaced boundary samples of a region (→ Point2Bundle) — for footprint clearance."""

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
from fungeom.primitives.region2.value import boundary_samples


@dataclass(frozen=True, eq=False)
class Region2Sample(Point2Bundle):
    """``samples`` points spaced evenly by arc length around ``region``'s boundary, keyed ``0..N-1``.

    The field is ``samples`` (not ``count``) so it does not shadow the inherited
    ``Bundle.count()`` method. Unresolvable for a non-positive count or an empty region.
    """

    region: Region2
    samples: int

    def _decide(self) -> BundleDecision[Point2Value]:
        match self.region.decide():
            case Resolvable(region):
                if self.samples < 1:
                    return Unresolvable(f"a region sample needs at least 1 point, got {self.samples}")
                if region.is_empty:
                    return Unresolvable("an empty region has no boundary to sample")
                coords = boundary_samples(region.rings, self.samples)
                members: dict[Hashable, Point2Value] = {
                    i: Point2Value(coord=coord, frame=WORLD_FRAME2) for i, coord in enumerate(coords)
                }
                return Resolvable(BundleValue(roster=tuple(range(len(coords))), members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
