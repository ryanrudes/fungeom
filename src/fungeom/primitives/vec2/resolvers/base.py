"""The ``Vec2`` interface and its algebra (mirrors ``vec3``)."""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.value import Float2


class Vec2(Resolver[Float2]):
    """A deferred 2D vector — the planar counterpart of :class:`~fungeom.Vec3`.

    Construct with :meth:`of` (components may be numbers or deferred
    :class:`~fungeom.Scalar`\\ s); compose with ``+``/``-``, :meth:`scale`,
    :meth:`norm`, :meth:`normalized`, :meth:`dot`, :meth:`cross` (the scalar
    perp-dot), :meth:`lerp`, :meth:`project_onto`, :meth:`reject_from`.
    ``resolve()`` yields a 2-element ``float64`` array (``Vec2.Value``).
    """

    type Value = Float2
    """The resolved value type — a 2-element ``float64`` array."""

    @classmethod
    def of(cls, x: float | Scalar = 0.0, y: float | Scalar = 0.0) -> Vec2:
        """A vector from components — a literal if all are numbers, a graph if any is a ``Scalar``."""
        literal: list[float] = []
        for component in (x, y):
            if isinstance(component, Scalar):
                from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
                from fungeom.primitives.vec2.resolvers.components import ComponentVec2

                return ComponentVec2(cx=as_scalar_resolver(x), cy=as_scalar_resolver(y))
            literal.append(component)

        from fungeom.primitives.vec2.resolvers.literal import LiteralVec2
        from fungeom.primitives.vec2.value import as_vec2

        return LiteralVec2(value=as_vec2(literal))

    def scale(self, factor: float | Scalar) -> Vec2:
        """This vector multiplied by a (deferred) scalar."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.vec2.resolvers.scaled import ScaledVec2

        return ScaledVec2(vector=self, factor=as_scalar_resolver(factor))

    def negate(self) -> Vec2:
        """The opposite vector."""
        return self.scale(-1.0)

    def norm(self) -> Scalar:
        """The Euclidean length of this vector, as a deferred scalar."""
        from fungeom.primitives.vec2.resolvers.norm import Vec2Norm

        return Vec2Norm(vector=self)

    def normalized(self) -> Vec2:
        """The unit vector in this direction (Unresolvable if this is zero)."""
        from fungeom.primitives.vec2.resolvers.normalized import NormalizedVec2

        return NormalizedVec2(vector=self)

    def dot(self, other: Vec2) -> Scalar:
        """The dot product with ``other``, as a deferred scalar."""
        from fungeom.primitives.vec2.resolvers.dot import Vec2Dot

        return Vec2Dot(a=self, b=other)

    def cross(self, other: Vec2) -> Scalar:
        """The scalar 2D cross product (signed area) with ``other``."""
        from fungeom.primitives.vec2.resolvers.dot import Vec2Cross

        return Vec2Cross(a=self, b=other)

    def project_onto(self, other: Vec2) -> Vec2:
        """This vector's component along ``other`` (Unresolvable if ``other`` is zero)."""
        from fungeom.primitives.vec2.resolvers.projected import ProjectedVec2

        return ProjectedVec2(a=self, onto=other)

    def reject_from(self, other: Vec2) -> Vec2:
        """This vector's component orthogonal to ``other`` (Unresolvable if ``other`` is zero)."""
        from fungeom.primitives.vec2.resolvers.projected import RejectedVec2

        return RejectedVec2(a=self, onto=other)

    def lerp(self, other: Vec2, t: float | Scalar) -> Vec2:
        """Linearly interpolate toward ``other`` (``t=0`` here, ``t=1`` there)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.vec2.resolvers.lerp import LerpVec2

        return LerpVec2(a=self, b=other, t=as_scalar_resolver(t))

    def x(self) -> Scalar:
        """The x component, as a deferred scalar."""
        from fungeom.primitives.vec2.resolvers.coordinate import Vec2Coordinate

        return Vec2Coordinate(vector=self, axis=0)

    def y(self) -> Scalar:
        """The y component, as a deferred scalar."""
        from fungeom.primitives.vec2.resolvers.coordinate import Vec2Coordinate

        return Vec2Coordinate(vector=self, axis=1)

    def angle_to(self, other: Vec2) -> Scalar:
        """The unsigned angle (radians) to ``other`` (Unresolvable if either vector is zero)."""
        from fungeom.primitives.vec2.resolvers.angle import Vec2Angle

        return Vec2Angle(a=self, b=other)

    def with_norm(self, length: float | Scalar) -> Vec2:
        """This direction rescaled to ``length`` (Unresolvable if this is the zero vector)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.vec2.resolvers.resized import ResizedVec2

        return ResizedVec2(vector=self, length=as_scalar_resolver(length))

    def perpendicular(self) -> Vec2:
        """This vector turned 90° counter-clockwise — ``(-y, x)``."""
        from fungeom.primitives.vec2.resolvers.perpendicular import PerpendicularVec2

        return PerpendicularVec2(vector=self)

    def __add__(self, other: Vec2) -> Vec2:
        from fungeom.primitives.vec2.resolvers.sum import SumVec2

        return SumVec2(a=self, b=other)

    def __sub__(self, other: Vec2) -> Vec2:
        from fungeom.primitives.vec2.resolvers.sum import SumVec2

        return SumVec2(a=self, b=other.negate())
