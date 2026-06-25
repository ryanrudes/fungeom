"""The ``Direction3`` interface and its algebra."""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.resolvers.base import Vec3


class Direction3(Resolver[Direction3Value]):
    """A deferred unit direction — a vector constrained to length 1.

    Construct with :meth:`of` (from components, normalized) or :meth:`towards`
    (the direction of a :class:`~fungeom.Vec3`); compose with
    :meth:`reversed`, :meth:`angle_to`, :meth:`slerp`, :meth:`as_vector`,
    :meth:`dot`, :meth:`cross`.
    ``resolve()`` yields a ``Direction3.Value``, whose ``vector`` is always unit
    length by construction.

    Building a direction is *partial*: the zero vector has no direction, and
    :meth:`slerp` is undefined for antipodal directions — see :meth:`decide`.
    """

    type Value = Direction3Value
    """The resolved value type — a unit-length direction."""

    @classmethod
    def of(cls, x: float | Scalar, y: float | Scalar, z: float | Scalar) -> Direction3:
        """A direction from components (normalized) — a graph if any component is a ``Scalar``.

        The zero vector has no direction; this constructor reports that uniformly
        as :class:`~fungeom.Unresolvable` (via :meth:`decide`), whether the
        components are literal or deferred — it never raises.
        """
        literal: list[float] = []
        for component in (x, y, z):
            if isinstance(component, Scalar):
                return cls.towards(Vec3.of(x, y, z))
            literal.append(component)

        if not any(literal):
            # the zero vector -> normalize it lazily so this is Unresolvable, not a raise
            return cls.towards(Vec3.of(literal[0], literal[1], literal[2]))

        from fungeom.primitives.direction3.resolvers.literal import LiteralDirection3

        return LiteralDirection3(value=Direction3Value.of(literal[0], literal[1], literal[2]))

    @classmethod
    def towards(cls, vector: Vec3) -> Direction3:
        """The direction of a (deferred) vector (Unresolvable at the origin)."""
        from fungeom.primitives.direction3.resolvers.normalized import NormalizedDirection3

        return NormalizedDirection3(vector=vector)

    def reversed(self) -> Direction3:
        """The opposite direction."""
        from fungeom.primitives.direction3.resolvers.reversed import ReversedDirection3

        return ReversedDirection3(direction=self)

    def angle_to(self, other: Direction3) -> Scalar:
        """The angle (radians) to ``other``, as a deferred scalar."""
        from fungeom.primitives.direction3.resolvers.angle import Direction3Angle

        return Direction3Angle(a=self, b=other)

    def slerp(self, other: Direction3, t: float | Scalar) -> Direction3:
        """Spherically interpolate toward ``other`` (Unresolvable if antipodal)."""
        from fungeom.primitives.direction3.resolvers.slerp import SlerpDirection3
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return SlerpDirection3(a=self, b=other, t=as_scalar_resolver(t))

    def as_vector(self) -> Vec3:
        """This direction as a (unit) vector resolver."""
        from fungeom.primitives.direction3.resolvers.vector import DirectionVec3

        return DirectionVec3(direction=self)

    def dot(self, other: Direction3) -> Scalar:
        """The dot product with ``other`` — the cosine of the angle between them."""
        from fungeom.primitives.direction3.resolvers.dot import Direction3Dot

        return Direction3Dot(a=self, b=other)

    def cross(self, other: Direction3) -> Direction3:
        """The unit direction perpendicular to both (Unresolvable if ``other`` is parallel)."""
        from fungeom.primitives.direction3.resolvers.cross import CrossDirection3

        return CrossDirection3(a=self, b=other)

    def signed_angle_to(self, other: Direction3, *, about: Direction3) -> Scalar:
        """The signed angle to ``other`` measured in the plane ⟂ ``about`` (RH; → ``Scalar``).

        Both directions are projected into the plane perpendicular to ``about``; the result is
        right-handed about ``about`` in ``(-π, π]``. Unresolvable if either direction is parallel
        to ``about`` (its in-plane component vanishes). The 3D companion to
        :meth:`Direction2.signed_angle_to`.
        """
        from fungeom.primitives.direction3.resolvers.signed_angle import Direction3SignedAngle

        return Direction3SignedAngle(source=self, target=other, axis=about)

    def any_perpendicular(self) -> Direction3:
        """Some unit direction perpendicular to this one (arbitrary but deterministic; total)."""
        from fungeom.primitives.direction3.resolvers.any_perpendicular import AnyPerpendicular

        return AnyPerpendicular(direction=self)
