"""The ``Line`` interface — an oriented line and its algebra.

A line is the natural home for axis geometry: project a point onto it, measure the
perpendicular distance, read off its direction, and — given points known to be in
order along it — recover which way the direction should point. Constructors fix the
line from a point + direction or from two points; the combinators return the matching
primitive (``Point3`` / ``Scalar`` / ``Bool`` / ``Direction3``). Sibling concrete
resolvers are imported lazily to keep module load acyclic; the lower-layer primitives
are imported normally.
"""

from __future__ import annotations

from collections.abc import Sequence

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.line.value import LineValue
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.resolvers.base import Scalar


class Line(Resolver[LineValue]):
    """A deferred oriented line — a point on it and a (meaningful) direction.

    Construct with :meth:`through` (point + direction) or :meth:`through_points` (two
    distinct points). Read it with :meth:`direction` / :meth:`origin`, :meth:`project`,
    :meth:`distance_to`, :meth:`contains`; and orient it to a known ordering of points
    with :meth:`direction_along`. ``resolve()`` yields a ``LineValue`` (``Line.Value``).

    Partial cases: :meth:`through_points` is ``Unresolvable`` for coincident points;
    :meth:`direction_along` for points that are not in coherent monotone order along the
    line.
    """

    type Value = LineValue
    """The resolved value type — an oriented :class:`LineValue`."""

    @classmethod
    def through(cls, point: Point3, direction: Direction3) -> Line:
        """The line through ``point`` along ``direction``."""
        from fungeom.primitives.line.resolvers.through import LineThrough

        return LineThrough(anchor=point, axis=direction)

    @classmethod
    def through_points(cls, a: Point3, b: Point3) -> Line:
        """The line through two points, directed ``a → b`` (Unresolvable if coincident)."""
        from fungeom.primitives.line.resolvers.through_points import LineThroughPoints

        return LineThroughPoints(a=a, b=b)

    def direction(self) -> Direction3:
        """This line's unit direction (→ ``Direction3``)."""
        from fungeom.primitives.line.resolvers.direction import LineDirection

        return LineDirection(line=self)

    def origin(self) -> Point3:
        """The line's representative point (→ ``Point3``)."""
        from fungeom.primitives.line.resolvers.origin import LineOrigin

        return LineOrigin(line=self)

    def project(self, point: Point3) -> Point3:
        """The orthogonal projection of ``point`` onto this line (→ ``Point3``)."""
        from fungeom.primitives.line.resolvers.project import LineProject

        return LineProject(line=self, point=point)

    def distance_to(self, point: Point3) -> Scalar:
        """The perpendicular distance from ``point`` to the line (→ ``Scalar``)."""
        from fungeom.primitives.line.resolvers.distance_to import LineDistanceTo

        return LineDistanceTo(line=self, point=point)

    def contains(self, point: Point3, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the line within ``tolerance`` (→ ``Bool``)."""
        return self.distance_to(point).le(tolerance)

    def direction_along(self, points: Sequence[Point3]) -> Direction3:
        """This line's direction, oriented to agree with ``points`` taken in order (→ ``Direction3``).

        The line-fit tangent's *orientation*: the points are projected onto the line and
        must fall in strictly monotone order along it. If their parameters increase, the
        line's own direction is returned; if they decrease, its reverse. Unresolvable when
        fewer than two points are given, or when they are not in coherent monotone order
        (a fold-back, a tie, or a degenerate projection).
        """
        from fungeom.primitives.line.resolvers.direction_along import LineDirectionAlong

        return LineDirectionAlong(line=self, points=tuple(points))

    def point_at(self, distance: float) -> Point3:
        """The point at signed arc-length ``distance`` from the origin along the direction (→ ``Point3``)."""
        from fungeom.primitives.line.resolvers.point_at import LinePointAt

        return LinePointAt(line=self, distance=distance)
