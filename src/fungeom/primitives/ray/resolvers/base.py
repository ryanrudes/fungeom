"""The ``Ray`` interface — a half-line and its algebra.

A ray is a line with a *start*: it begins at an origin and extends one way only. That
single restriction — non-negative parameters — is what makes it the right model for an
outward surface normal, a sensor or camera ray, or an "is this in front of me?" test.
Its combinators mirror :class:`~fungeom.Line`, but ``project`` / ``distance_to`` clamp
behind the origin and ``point_at`` refuses a negative distance. Sibling concrete
resolvers are imported lazily; the lower-layer primitives are imported normally.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.ray.value import RayValue
from fungeom.primitives.scalar.resolvers.base import Scalar


class Ray(Resolver[RayValue]):
    """A deferred half-line — an origin and the direction it extends in.

    Construct with :meth:`through` (origin + direction) or :meth:`from_to` (origin +
    a point it aims at). Read it with :meth:`origin` / :meth:`direction`,
    :meth:`project`, :meth:`distance_to`, :meth:`contains`, and :meth:`point_at` (march a
    non-negative distance from the origin); flip it with :meth:`reversed`.
    ``resolve()`` yields a ``RayValue`` (``Ray.Value``).

    Partial cases: :meth:`from_to` is ``Unresolvable`` when the target coincides with the
    origin; :meth:`point_at` for a negative distance (off the half-line).
    """

    type Value = RayValue
    """The resolved value type — a :class:`RayValue` half-line."""

    @classmethod
    def through(cls, origin: Point3, direction: Direction3) -> Ray:
        """The ray from ``origin`` extending along ``direction``."""
        from fungeom.primitives.ray.resolvers.through import RayThrough

        return RayThrough(anchor=origin, axis=direction)

    @classmethod
    def from_to(cls, origin: Point3, target: Point3) -> Ray:
        """The ray from ``origin`` aimed at ``target`` (Unresolvable if they coincide)."""
        from fungeom.primitives.ray.resolvers.from_to import RayFromTo

        return RayFromTo(source=origin, target=target)

    def origin(self) -> Point3:
        """The ray's start point (→ ``Point3``)."""
        from fungeom.primitives.ray.resolvers.origin import RayOrigin

        return RayOrigin(ray=self)

    def direction(self) -> Direction3:
        """The ray's unit direction (→ ``Direction3``)."""
        from fungeom.primitives.ray.resolvers.direction import RayDirection

        return RayDirection(ray=self)

    def project(self, point: Point3) -> Point3:
        """The closest point of the ray to ``point`` (the origin if it is behind → ``Point3``)."""
        from fungeom.primitives.ray.resolvers.project import RayProject

        return RayProject(ray=self, point=point)

    def distance_to(self, point: Point3) -> Scalar:
        """The distance from ``point`` to the ray (→ ``Scalar``; to the origin if behind)."""
        from fungeom.primitives.ray.resolvers.distance_to import RayDistanceTo

        return RayDistanceTo(ray=self, point=point)

    def contains(self, point: Point3, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the ray within ``tolerance`` (→ ``Bool``)."""
        return self.distance_to(point).le(tolerance)

    def point_at(self, distance: float) -> Point3:
        """The point ``distance`` along the ray from the origin (Unresolvable if negative → ``Point3``)."""
        from fungeom.primitives.ray.resolvers.point_at import RayPointAt

        return RayPointAt(ray=self, distance=distance)

    def reversed(self) -> Ray:
        """The opposite half-line from the same origin."""
        from fungeom.primitives.ray.resolvers.reversed import RayReversed

        return RayReversed(ray=self)

    def intersect(self, plane: Plane) -> Point3:
        """Where this ray first meets ``plane`` (the raycast → ``Point3``).

        Unresolvable when the ray is parallel to the plane, or when the plane lies behind
        the ray's origin (the ray points away from it).
        """
        from fungeom.primitives.ray.resolvers.intersect import RayPlaneIntersection

        return RayPlaneIntersection(ray=self, plane=plane)
