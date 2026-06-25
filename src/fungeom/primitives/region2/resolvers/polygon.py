"""A simple-polygon region from ordered points (gathers its vertices)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.value import Region2Value, oriented_ccw, ring_is_simple, ring_signed_area


@dataclass(frozen=True, eq=False)
class PolygonRegion2(Region2):
    """The simple polygon through ``points`` in order — oriented counter-clockwise.

    Unresolvable if any vertex is (an occluded marker propagates), if there are fewer than
    three distinct vertices, if consecutive vertices coincide, if the loop encloses no area
    (collinear), or if it is self-intersecting (not a simple polygon).
    """

    points: tuple[Point2, ...]

    def _decide(self) -> Region2Decision:
        coords = []
        for point in self.points:
            decision = point.decide()
            if isinstance(decision, Unresolvable):
                return decision
            coords.append(decision.value.coord)
        if len(coords) < 3:
            return Unresolvable(f"a polygon needs at least 3 vertices, got {len(coords)}")
        ring = np.array(coords)
        if np.any(np.all(np.isclose(ring, np.roll(ring, -1, axis=0)), axis=1)):
            return Unresolvable("a polygon has coincident consecutive vertices")
        if abs(ring_signed_area(ring)) <= 1e-12:
            return Unresolvable("a polygon encloses no area (its vertices are collinear)")
        if not ring_is_simple(ring):
            return Unresolvable("the polygon is self-intersecting (not a simple polygon)")
        return Resolvable(Region2Value(rings=(oriented_ccw(ring),)))
