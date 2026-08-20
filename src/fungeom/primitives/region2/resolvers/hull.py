"""The convex hull of points — from a raw sequence or a ``Point2Bundle`` (an exact combinatorial fit)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import ConvexHull, QhullError

from fungeom.core.resolvability import Resolvable, Resolvability, Unresolvable
from fungeom.primitives.bundle.resolvers.point2 import Point2Bundle
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.value import Region2Value


def _hull_of(coords: list[np.ndarray]) -> Resolvability[Region2Value]:
    """The convex hull of ``coords`` as a CCW polygon region — Unresolvable if < 3 non-collinear."""
    if len(coords) < 3:
        return Unresolvable(f"a convex hull needs at least 3 points, got {len(coords)}")
    points = np.array(coords)
    try:
        hull = ConvexHull(points)
    except (QhullError, ValueError):
        return Unresolvable("the points have no 2D convex hull (collinear or coincident)")
    return Resolvable(Region2Value(rings=(points[hull.vertices],)))  # hull.vertices are CCW in 2D


@dataclass(frozen=True, eq=False)
class HullRegion2(Region2):
    """The convex hull of a sequence of ``Point2``s — Unresolvable if any is, or < 3 non-collinear."""

    points: tuple[Point2, ...]

    def _decide(self) -> Region2Decision:
        coords = []
        for point in self.points:
            decision = point.decide()
            if isinstance(decision, Unresolvable):
                return decision
            coords.append(decision.value.coord)
        return _hull_of(coords)


@dataclass(frozen=True, eq=False)
class BundleHullRegion2(Region2):
    """The convex hull of the *present* members of a ``Point2Bundle`` — the markers-to-patch step."""

    cloud: Point2Bundle

    def _decide(self) -> Region2Decision:
        decision = self.cloud.decide()
        if isinstance(decision, Unresolvable):
            return decision
        collection = decision.value
        coords = [collection.members[key].coord for key in collection.support()]
        return _hull_of(coords)


@dataclass(frozen=True, eq=False)
class TolerantBundleHullRegion2(Region2):
    """:class:`BundleHullRegion2` with the degeneracy test made *tolerance-based* rather than exact.

    ``_hull_of`` refuses only what Qhull refuses — points that are collinear or coincident
    *exactly*. That is the right test when the 2-D points are given; it is the wrong one when they
    are the **projection** of a 3-D cloud into a chart chosen elsewhere, because a cloud that misses
    collinearity by a floating-point hair still yields a sliver hull whose area, centroid and
    boundary are numerical noise. The test here is the same shape as the plane fit's
    (``fit_plane_coords``): the spread perpendicular to the cloud's principal chart direction must
    exceed ``tolerance`` times its scale, so *near*-collinear is refused too.

    Used by ``Point3BundleSignal.hull_in``, where the plane comes from outside and may be tilted
    with respect to the cloud — the case that makes near-collinear projections reachable at all.
    """

    cloud: Point2Bundle
    tolerance: float

    def _decide(self) -> Region2Decision:
        decision = self.cloud.decide()
        if isinstance(decision, Unresolvable):
            return decision
        collection = decision.value
        coords = [collection.members[key].coord for key in collection.support()]
        if len(coords) >= 3:
            points = np.asarray(coords, dtype=float)
            singular = np.linalg.svd(points - points.mean(axis=0), compute_uv=False)
            if singular[1] <= self.tolerance * singular[0]:
                return Unresolvable(
                    "the points are collinear within tolerance in this chart (no two-dimensional footprint)"
                )
        return _hull_of(coords)
