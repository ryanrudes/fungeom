"""The ``Segment2`` interface — a finite 2D line segment and its algebra (the planar ``Segment``)."""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.segment2.value import Segment2Value


class Segment2(Resolver[Segment2Value]):
    """A deferred finite 2D segment — two endpoints and everything bounded between them.

    Construct with :meth:`between` (two points). Read the ends with :meth:`start` /
    :meth:`end`, its shape with :meth:`direction` / :meth:`length` / :meth:`midpoint`,
    and query it with :meth:`project`, :meth:`distance_to`, :meth:`contains`, :meth:`at`
    (a parameter in ``[0, 1]``), and :meth:`parameter_of`; flip it with :meth:`reversed`.
    ``resolve()`` yields a ``Segment2Value`` (``Segment2.Value``).

    Partial cases: :meth:`direction` is ``Unresolvable`` for a degenerate (zero-length)
    segment; :meth:`at` for a parameter outside ``[0, 1]``.
    """

    type Value = Segment2Value
    """The resolved value type — a :class:`Segment2Value`."""

    @classmethod
    def between(cls, start: Point2, end: Point2) -> Segment2:
        """The segment from ``start`` to ``end``."""
        from fungeom.primitives.segment2.resolvers.between import Segment2Between

        return Segment2Between(a=start, b=end)

    def start(self) -> Point2:
        """The segment's start endpoint (→ ``Point2``)."""
        from fungeom.primitives.segment2.resolvers.endpoints import Segment2Start

        return Segment2Start(segment=self)

    def end(self) -> Point2:
        """The segment's end endpoint (→ ``Point2``)."""
        from fungeom.primitives.segment2.resolvers.endpoints import Segment2End

        return Segment2End(segment=self)

    def direction(self) -> Direction2:
        """The unit direction from start to end (Unresolvable if degenerate → ``Direction2``)."""
        from fungeom.primitives.segment2.resolvers.direction import Segment2Direction

        return Segment2Direction(segment=self)

    def length(self) -> Scalar:
        """The segment's length (→ ``Scalar``; zero for a degenerate segment)."""
        from fungeom.primitives.segment2.resolvers.length import Segment2Length

        return Segment2Length(segment=self)

    def midpoint(self) -> Point2:
        """The point halfway along the segment (→ ``Point2``)."""
        from fungeom.primitives.segment2.resolvers.midpoint import Segment2Midpoint

        return Segment2Midpoint(segment=self)

    def project(self, point: Point2) -> Point2:
        """The closest point of the segment to ``point`` (clamped to the endpoints → ``Point2``)."""
        from fungeom.primitives.segment2.resolvers.project import Segment2Project

        return Segment2Project(segment=self, point=point)

    def distance_to(self, point: Point2) -> Scalar:
        """The distance from ``point`` to the segment (→ ``Scalar``)."""
        from fungeom.primitives.segment2.resolvers.distance_to import Segment2DistanceTo

        return Segment2DistanceTo(segment=self, point=point)

    def contains(self, point: Point2, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the segment within ``tolerance`` (→ ``Bool``)."""
        return self.distance_to(point).le(tolerance)

    def at(self, t: float) -> Point2:
        """The point at parameter ``t`` along the segment (Unresolvable outside ``[0, 1]`` → ``Point2``)."""
        from fungeom.primitives.segment2.resolvers.at import Segment2At

        return Segment2At(segment=self, t=t)

    def parameter_of(self, point: Point2) -> Scalar:
        """The clamped parameter in ``[0, 1]`` of ``point``'s closest point (→ ``Scalar``)."""
        from fungeom.primitives.segment2.resolvers.parameter_of import Segment2ParameterOf

        return Segment2ParameterOf(segment=self, point=point)

    def reversed(self) -> Segment2:
        """The same segment with its endpoints swapped."""
        from fungeom.primitives.segment2.resolvers.reversed import Segment2Reversed

        return Segment2Reversed(segment=self)
