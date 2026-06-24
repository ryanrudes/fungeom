"""The ``Line2`` interface — an oriented 2D line (a planar hyperplane) and its algebra.

In the plane a line is a hyperplane, so ``Line2`` offers *both* line algebra (direction,
projection, distance along) and plane algebra (a normal, a signed distance, a half-plane
side). Constructors fix it from a point + direction or from two points; the combinators
return the matching 2D primitive. Sibling concrete resolvers are imported lazily; the
lower-layer primitives are imported normally.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.line2.value import Line2Value
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.scalar.resolvers.base import Scalar


class Line2(Resolver[Line2Value]):
    """A deferred oriented 2D line — a point on it and the direction it runs.

    Construct with :meth:`through` (point + direction) or :meth:`through_points` (two
    distinct points). Read it with :meth:`direction` / :meth:`origin` / :meth:`normal`,
    project with :meth:`project`, and measure with :meth:`distance_to` (unsigned),
    :meth:`signed_distance` (positive on the left-normal side), and :meth:`contains`.
    ``resolve()`` yields a ``Line2Value`` (``Line2.Value``).

    Partial case: :meth:`through_points` is ``Unresolvable`` for coincident points.
    """

    type Value = Line2Value
    """The resolved value type — an oriented :class:`Line2Value`."""

    @classmethod
    def through(cls, point: Point2, direction: Direction2) -> Line2:
        """The line through ``point`` along ``direction``."""
        from fungeom.primitives.line2.resolvers.through import Line2Through

        return Line2Through(anchor=point, axis=direction)

    @classmethod
    def through_points(cls, a: Point2, b: Point2) -> Line2:
        """The line through two points, directed ``a → b`` (Unresolvable if coincident)."""
        from fungeom.primitives.line2.resolvers.through_points import Line2ThroughPoints

        return Line2ThroughPoints(a=a, b=b)

    def direction(self) -> Direction2:
        """This line's unit direction (→ ``Direction2``)."""
        from fungeom.primitives.line2.resolvers.direction import Line2Direction

        return Line2Direction(line=self)

    def origin(self) -> Point2:
        """The line's representative point (→ ``Point2``)."""
        from fungeom.primitives.line2.resolvers.origin import Line2Origin

        return Line2Origin(line=self)

    def normal(self) -> Direction2:
        """The line's unit left normal — a quarter turn from the direction (→ ``Direction2``)."""
        from fungeom.primitives.line2.resolvers.normal import Line2Normal

        return Line2Normal(line=self)

    def project(self, point: Point2) -> Point2:
        """The orthogonal projection of ``point`` onto this line (→ ``Point2``)."""
        from fungeom.primitives.line2.resolvers.project import Line2Project

        return Line2Project(line=self, point=point)

    def signed_distance(self, point: Point2) -> Scalar:
        """The signed distance from ``point`` to the line (positive on the left-normal side)."""
        from fungeom.primitives.line2.resolvers.signed_distance import Line2SignedDistance

        return Line2SignedDistance(line=self, point=point)

    def distance_to(self, point: Point2) -> Scalar:
        """The unsigned perpendicular distance from ``point`` to the line (→ ``Scalar``)."""
        from fungeom.primitives.line2.resolvers.distance_to import Line2DistanceTo

        return Line2DistanceTo(line=self, point=point)

    def contains(self, point: Point2, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the line within ``tolerance`` (→ ``Bool``)."""
        return self.distance_to(point).le(tolerance)
