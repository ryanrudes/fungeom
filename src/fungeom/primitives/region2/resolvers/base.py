"""The ``Region2`` interface — a bounded planar region and its algebra.

The bounded-area member of the 2D family (``point2``/``segment2``/``frame2``/…): the 2D
spatial sibling of the temporal ``Interval``/``Coverage``. A region is built (``rectangle`` /
``disc`` / ``polygon`` / ``hull``), queried (``contains`` / ``area`` / ``centroid`` /
``vertices``), and reshaped (``transformed_by``, and — later rungs — ``offset`` and the
boolean ``union`` / ``intersection`` / ``difference``). Coordinates are bare 2D numbers in a
region-local chart; a ``Plane`` / ``Face`` supplies the 3D embedding. Degenerate inputs are
``Unresolvable``, never exceptions. Sibling concrete resolvers are imported lazily; the
lower-layer primitives are imported normally.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.region2.value import Region2Value
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.resolvers.base import Transform2

if TYPE_CHECKING:
    from fungeom.primitives.bundle.resolvers.point2 import Point2Bundle


class Region2(Resolver[Region2Value]):
    """A deferred bounded planar region — a polygonal area in a local 2D chart.

    Construct with :meth:`rectangle`, :meth:`disc`, :meth:`polygon` (a simple polygon), or
    :meth:`hull` (the convex hull of points / a ``Point2Bundle``). Query with
    :meth:`contains` (→ ``Bool``), :meth:`area` (→ ``Scalar``), :meth:`centroid` (→
    ``Point2``), :meth:`vertices` (→ ``Point2Bundle``). Reshape with :meth:`transformed_by`.
    ``resolve()`` yields a ``Region2Value`` (``Region2.Value``).

    Partial cases: a non-positive ``rectangle``/``disc`` extent; a ``polygon`` that is
    self-intersecting, has fewer than three vertices, or encloses no area; a ``hull`` of
    fewer than three non-collinear present points; :meth:`centroid` of an empty region.
    """

    type Value = Region2Value
    """The resolved value type — a :class:`Region2Value` polygonal area."""

    empty: ClassVar[Region2]
    """The empty region (no area) — the identity for :meth:`union`. (Assigned once ``LiteralRegion2`` exists.)"""

    @classmethod
    def rectangle(cls, width: float, height: float, center: Sequence[float] = (0.0, 0.0)) -> Region2:
        """An axis-aligned rectangle of size ``width × height`` about ``center`` (Unresolvable if non-positive)."""
        from fungeom.primitives.region2.resolvers.rectangle import RectangleRegion2

        cx, cy = center
        return RectangleRegion2(width=width, height=height, cx=cx, cy=cy)

    @classmethod
    def disc(cls, radius: float, center: Sequence[float] = (0.0, 0.0), segments: int = 64) -> Region2:
        """A disc of ``radius`` about ``center``, approximated by a ``segments``-gon (Unresolvable if non-positive)."""
        from fungeom.primitives.region2.resolvers.disc import DiscRegion2

        cx, cy = center
        return DiscRegion2(radius=radius, cx=cx, cy=cy, segments=segments)

    @classmethod
    def polygon(cls, points: Sequence[Point2]) -> Region2:
        """A simple polygon through ``points`` in order (Unresolvable if self-intersecting / degenerate)."""
        from fungeom.primitives.region2.resolvers.polygon import PolygonRegion2

        return PolygonRegion2(points=tuple(points))

    @classmethod
    def hull(cls, points: Point2Bundle | Sequence[Point2]) -> Region2:
        """The convex hull of ``points`` (a sequence or a ``Point2Bundle``); Unresolvable if < 3 non-collinear."""
        from fungeom.primitives.bundle.resolvers.point2 import Point2Bundle
        from fungeom.primitives.region2.resolvers.hull import BundleHullRegion2, HullRegion2

        if isinstance(points, Point2Bundle):
            return BundleHullRegion2(cloud=points)
        return HullRegion2(points=tuple(points))

    def contains(self, point: Point2) -> Bool:
        """Whether ``point`` lies in this region, boundary included (→ ``Bool``)."""
        from fungeom.primitives.region2.resolvers.contains import Region2Contains

        return Region2Contains(region=self, point=point)

    def area(self) -> Scalar:
        """This region's total area — outer rings minus holes (→ ``Scalar``; ``0`` if empty)."""
        from fungeom.primitives.region2.resolvers.area import Region2Area

        return Region2Area(region=self)

    def centroid(self) -> Point2:
        """The area-weighted centroid (→ ``Point2``; Unresolvable for an empty / zero-area region)."""
        from fungeom.primitives.region2.resolvers.centroid import Region2Centroid

        return Region2Centroid(region=self)

    def vertices(self) -> Point2Bundle:
        """The region's boundary vertices, keyed ``0..N-1`` in ring order (→ ``Point2Bundle``)."""
        from fungeom.primitives.region2.resolvers.vertices import Region2Vertices

        return Region2Vertices(region=self)

    def bounds(self) -> Point2Bundle:
        """The axis-aligned bounding box as a ``{'min', 'max'}`` corner cloud (→ ``Point2Bundle``; Unresolvable if empty)."""
        from fungeom.primitives.region2.resolvers.bounds import Region2Bounds

        return Region2Bounds(region=self)

    def signed_distance(self, point: Point2) -> Scalar:
        """The signed distance from ``point`` to this region — positive inside, negative outside (→ ``Scalar``).

        The balance-board / ZMP stability margin: how deep inside (or far outside) the support
        polygon a point lies. Unresolvable for an empty region.
        """
        from fungeom.primitives.region2.resolvers.signed_distance import Region2SignedDistance

        return Region2SignedDistance(region=self, point=point)

    def nearest_boundary_point(self, point: Point2) -> Point2:
        """The point on this region's boundary closest to ``point`` (→ ``Point2``; Unresolvable if empty)."""
        from fungeom.primitives.region2.resolvers.nearest_boundary import Region2NearestBoundaryPoint

        return Region2NearestBoundaryPoint(region=self, point=point)

    def union(self, other: Region2) -> Region2:
        """The union of this region and ``other`` (→ ``Region2``; general, via GEOS).

        Disjoint regions become a multipolygon; overlapping outlines merge; a contained region is
        swallowed. Total — only an ``Unresolvable`` operand propagates.
        """
        from fungeom.primitives.region2.resolvers.boolean import UnionRegion2

        return UnionRegion2(a=self, b=other)

    def intersection(self, other: Region2) -> Region2:
        """The overlap of this region and ``other`` (→ ``Region2``; general, via GEOS; empty if they don't meet)."""
        from fungeom.primitives.region2.resolvers.boolean import IntersectionRegion2

        return IntersectionRegion2(a=self, b=other)

    def difference(self, other: Region2) -> Region2:
        """This region minus ``other`` (→ ``Region2``; general, via GEOS).

        A contained ``other`` is punched out as a hole; a partial overlap clips correctly; a
        disjoint ``other`` leaves this region unchanged; ``other`` enclosing this → empty.
        """
        from fungeom.primitives.region2.resolvers.boolean import DifferenceRegion2

        return DifferenceRegion2(a=self, b=other)

    def sample(self, count: int) -> Point2Bundle:
        """``count`` points spaced evenly by arc length around the boundary (→ ``Point2Bundle``).

        Deterministic ordering (keyed ``0..count-1``), for footprint clearance sampling.
        Unresolvable for a non-positive ``count`` or an empty region.
        """
        from fungeom.primitives.region2.resolvers.sample import Region2Sample

        return Region2Sample(region=self, samples=count)

    def corners(self) -> Point2Bundle:
        """The region's boundary vertices (→ ``Point2Bundle``) — an alias of :meth:`vertices`."""
        return self.vertices()

    def offset(self, distance: float) -> Region2:
        """This region grown (``distance`` > 0) or eroded (< 0) by ``distance`` (→ ``Region2``).

        A general Minkowski buffer (via GEOS, rounded joins) — works on any region, including
        non-convex and holey ones; erosion past extinction yields the empty region. Total.
        """
        from fungeom.primitives.region2.resolvers.offset import OffsetRegion2

        return OffsetRegion2(region=self, distance=distance)

    def transformed_by(self, transform: Transform2) -> Region2:
        """This region moved by a rigid 2D ``transform`` (a motion in the chart)."""
        from fungeom.primitives.region2.resolvers.transformed import TransformedRegion2

        return TransformedRegion2(region=self, transform=transform)
