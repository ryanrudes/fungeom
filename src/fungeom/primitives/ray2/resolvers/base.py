"""The ``Ray2`` interface — a 2D half-line and its algebra (the planar ``Ray``)."""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.ray2.value import Ray2Value
from fungeom.primitives.scalar.resolvers.base import Scalar


class Ray2(Resolver[Ray2Value]):
    """A deferred 2D half-line — an origin and the direction it extends in.

    Construct with :meth:`through` (origin + direction) or :meth:`from_to` (origin + a
    point it aims at). Read it with :meth:`origin` / :meth:`direction`, :meth:`project`,
    :meth:`distance_to`, :meth:`contains`, and :meth:`point_at`; flip it with
    :meth:`reversed`. ``project`` / ``distance_to`` clamp behind the origin.

    Partial cases: :meth:`from_to` is ``Unresolvable`` for a coincident origin/target;
    :meth:`point_at` for a negative distance.
    """

    type Value = Ray2Value
    """The resolved value type — a :class:`Ray2Value` half-line."""

    @classmethod
    def through(cls, origin: Point2, direction: Direction2) -> Ray2:
        """The ray from ``origin`` extending along ``direction``."""
        from fungeom.primitives.ray2.resolvers.through import Ray2Through

        return Ray2Through(anchor=origin, axis=direction)

    @classmethod
    def from_to(cls, origin: Point2, target: Point2) -> Ray2:
        """The ray from ``origin`` aimed at ``target`` (Unresolvable if they coincide)."""
        from fungeom.primitives.ray2.resolvers.from_to import Ray2FromTo

        return Ray2FromTo(source=origin, target=target)

    def origin(self) -> Point2:
        """The ray's start point (→ ``Point2``)."""
        from fungeom.primitives.ray2.resolvers.origin import Ray2Origin

        return Ray2Origin(ray=self)

    def direction(self) -> Direction2:
        """The ray's unit direction (→ ``Direction2``)."""
        from fungeom.primitives.ray2.resolvers.direction import Ray2Direction

        return Ray2Direction(ray=self)

    def project(self, point: Point2) -> Point2:
        """The closest point of the ray to ``point`` (the origin if it is behind → ``Point2``)."""
        from fungeom.primitives.ray2.resolvers.project import Ray2Project

        return Ray2Project(ray=self, point=point)

    def distance_to(self, point: Point2) -> Scalar:
        """The distance from ``point`` to the ray (→ ``Scalar``; to the origin if behind)."""
        from fungeom.primitives.ray2.resolvers.distance_to import Ray2DistanceTo

        return Ray2DistanceTo(ray=self, point=point)

    def contains(self, point: Point2, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the ray within ``tolerance`` (→ ``Bool``)."""
        return self.distance_to(point).le(tolerance)

    def point_at(self, distance: float) -> Point2:
        """The point ``distance`` along the ray from the origin (Unresolvable if negative → ``Point2``)."""
        from fungeom.primitives.ray2.resolvers.point_at import Ray2PointAt

        return Ray2PointAt(ray=self, distance=distance)

    def reversed(self) -> Ray2:
        """The opposite half-line from the same origin."""
        from fungeom.primitives.ray2.resolvers.reversed import Ray2Reversed

        return Ray2Reversed(ray=self)

    def intersect(self, line: Line2) -> Point2:
        """Where this ray first meets ``line`` (the planar raycast → ``Point2``).

        Unresolvable when the ray is parallel to the line, or when the line lies behind the
        ray's origin (the ray points away from it).
        """
        from fungeom.primitives.ray2.resolvers.intersect import Ray2LineIntersection

        return Ray2LineIntersection(ray=self, line=line)
