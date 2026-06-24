"""The ``Segment`` interface — a finite line segment and its algebra.

A segment is the bounded line: it runs from one endpoint to another and stops. That is
exactly a bone (joint to joint), a chord, or any finite span — so it carries length and
a midpoint, and its ``project`` clamps to the endpoints (the closest point on a *bone*,
not on its infinite extension). Constructors fix it from two points; the combinators
return the matching primitive. Sibling concrete resolvers are imported lazily; the
lower-layer primitives are imported normally.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.segment.value import SegmentValue


class Segment(Resolver[SegmentValue]):
    """A deferred finite segment — two endpoints and everything bounded between them.

    Construct with :meth:`between` (two points). Read the ends with :meth:`start` /
    :meth:`end`, its shape with :meth:`direction` / :meth:`length` / :meth:`midpoint`,
    and query it with :meth:`project`, :meth:`distance_to`, :meth:`contains`, :meth:`at`
    (a parameter in ``[0, 1]``), and :meth:`parameter_of`; flip it with :meth:`reversed`.
    ``resolve()`` yields a ``SegmentValue`` (``Segment.Value``).

    Partial cases: :meth:`direction` is ``Unresolvable`` for a degenerate (zero-length)
    segment; :meth:`at` for a parameter outside ``[0, 1]`` (off the segment).
    """

    type Value = SegmentValue
    """The resolved value type — a :class:`SegmentValue`."""

    @classmethod
    def between(cls, start: Point3, end: Point3) -> Segment:
        """The segment from ``start`` to ``end``."""
        from fungeom.primitives.segment.resolvers.between import SegmentBetween

        return SegmentBetween(a=start, b=end)

    def start(self) -> Point3:
        """The segment's start endpoint (→ ``Point3``)."""
        from fungeom.primitives.segment.resolvers.endpoints import SegmentStart

        return SegmentStart(segment=self)

    def end(self) -> Point3:
        """The segment's end endpoint (→ ``Point3``)."""
        from fungeom.primitives.segment.resolvers.endpoints import SegmentEnd

        return SegmentEnd(segment=self)

    def direction(self) -> Direction3:
        """The unit direction from start to end (Unresolvable if degenerate → ``Direction3``)."""
        from fungeom.primitives.segment.resolvers.direction import SegmentDirection

        return SegmentDirection(segment=self)

    def length(self) -> Scalar:
        """The segment's length (→ ``Scalar``; zero for a degenerate segment)."""
        from fungeom.primitives.segment.resolvers.length import SegmentLength

        return SegmentLength(segment=self)

    def midpoint(self) -> Point3:
        """The point halfway along the segment (→ ``Point3``)."""
        from fungeom.primitives.segment.resolvers.midpoint import SegmentMidpoint

        return SegmentMidpoint(segment=self)

    def project(self, point: Point3) -> Point3:
        """The closest point of the segment to ``point`` (clamped to the endpoints → ``Point3``)."""
        from fungeom.primitives.segment.resolvers.project import SegmentProject

        return SegmentProject(segment=self, point=point)

    def distance_to(self, point: Point3) -> Scalar:
        """The distance from ``point`` to the segment (→ ``Scalar``)."""
        from fungeom.primitives.segment.resolvers.distance_to import SegmentDistanceTo

        return SegmentDistanceTo(segment=self, point=point)

    def contains(self, point: Point3, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the segment within ``tolerance`` (→ ``Bool``)."""
        return self.distance_to(point).le(tolerance)

    def at(self, t: float) -> Point3:
        """The point at parameter ``t`` along the segment (Unresolvable outside ``[0, 1]`` → ``Point3``)."""
        from fungeom.primitives.segment.resolvers.at import SegmentAt

        return SegmentAt(segment=self, t=t)

    def parameter_of(self, point: Point3) -> Scalar:
        """The clamped parameter in ``[0, 1]`` of ``point``'s closest point (→ ``Scalar``)."""
        from fungeom.primitives.segment.resolvers.parameter_of import SegmentParameterOf

        return SegmentParameterOf(segment=self, point=point)

    def reversed(self) -> Segment:
        """The same segment with its endpoints swapped."""
        from fungeom.primitives.segment.resolvers.reversed import SegmentReversed

        return SegmentReversed(segment=self)
