"""The ``Direction2`` interface and its algebra — the 2D sibling of ``Direction3``."""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.resolvers.base import Vec2


class Direction2(Resolver[Direction2Value]):
    """A deferred unit 2D direction — a planar vector constrained to length 1.

    Construct with :meth:`of` (from components, normalized), :meth:`towards` (the
    direction of a :class:`~fungeom.Vec2`), or :meth:`from_angle` (an angle off +x);
    compose with :meth:`reversed`, :meth:`perpendicular`, :meth:`angle`,
    :meth:`angle_to`, :meth:`dot`, :meth:`as_vector`. ``resolve()`` yields a
    ``Direction2.Value``, whose ``vector`` is always unit length by construction.

    Building a direction is *partial*: the zero vector has no direction (reported
    uniformly through :meth:`decide`, never raised).
    """

    type Value = Direction2Value
    """The resolved value type — a unit-length 2D direction."""

    @classmethod
    def of(cls, x: float | Scalar, y: float | Scalar) -> Direction2:
        """A direction from components (normalized) — a graph if any component is a ``Scalar``.

        The zero vector has no direction; this constructor reports that uniformly as
        :class:`~fungeom.Unresolvable` (via :meth:`decide`), never raising.
        """
        for component in (x, y):
            if isinstance(component, Scalar):
                return cls.towards(Vec2.of(x, y))
        if not any((x, y)):
            return cls.towards(Vec2.of(x, y))

        from fungeom.primitives.direction2.resolvers.literal import LiteralDirection2

        return LiteralDirection2(value=Direction2Value.of(float(x), float(y)))  # type: ignore[arg-type]

    @classmethod
    def towards(cls, vector: Vec2) -> Direction2:
        """The direction of a (deferred) vector (Unresolvable at the origin)."""
        from fungeom.primitives.direction2.resolvers.normalized import NormalizedDirection2

        return NormalizedDirection2(vector=vector)

    @classmethod
    def from_angle(cls, angle: float) -> Direction2:
        """The unit direction at ``angle`` radians from +x (counter-clockwise)."""
        from fungeom.primitives.direction2.resolvers.literal import LiteralDirection2

        return LiteralDirection2(value=Direction2Value.from_angle(angle))

    def reversed(self) -> Direction2:
        """The opposite direction."""
        from fungeom.primitives.direction2.resolvers.reversed import ReversedDirection2

        return ReversedDirection2(direction=self)

    def perpendicular(self) -> Direction2:
        """The left perpendicular — a quarter turn counter-clockwise (total)."""
        from fungeom.primitives.direction2.resolvers.perpendicular import PerpendicularDirection2

        return PerpendicularDirection2(direction=self)

    def angle(self) -> Scalar:
        """This direction's angle (radians) from +x, in ``(-π, π]`` (→ ``Scalar``)."""
        from fungeom.primitives.direction2.resolvers.angle import Direction2OrientedAngle

        return Direction2OrientedAngle(direction=self)

    def angle_to(self, other: Direction2) -> Scalar:
        """The unsigned angle (radians) to ``other``, as a deferred scalar."""
        from fungeom.primitives.direction2.resolvers.angle_to import Direction2AngleTo

        return Direction2AngleTo(a=self, b=other)

    def dot(self, other: Direction2) -> Scalar:
        """The dot product with ``other`` — the cosine of the angle between them."""
        from fungeom.primitives.direction2.resolvers.dot import Direction2Dot

        return Direction2Dot(a=self, b=other)

    def as_vector(self) -> Vec2:
        """This direction as a (unit) vector resolver."""
        from fungeom.primitives.direction2.resolvers.vector import Direction2Vec2

        return Direction2Vec2(direction=self)
