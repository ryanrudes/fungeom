"""The ``Vec3`` interface and its algebra."""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.value import Float3


class Vec3(Resolver[Float3]):
    """A deferred 3D vector (a frame-free displacement).

    Construct with :meth:`of` — components may be plain numbers *or* deferred
    :class:`~fungeom.Scalar`\\ s. Compose with ``+``/``-``, :meth:`scale`,
    :meth:`norm`, :meth:`normalized`, :meth:`dot`, :meth:`cross`, :meth:`lerp`,
    :meth:`project_onto`, :meth:`reject_from`; each returns a new resolver
    (:meth:`norm`/:meth:`dot` return a :class:`~fungeom.Scalar`).
    ``resolve()`` yields a 3-element ``float64`` array (``Vec3.Value``).

    :meth:`normalized` and projection are *partial* at the origin (the zero
    vector has no direction) — see :meth:`decide`.
    """

    type Value = Float3
    """The resolved value type — a 3-element ``float64`` array."""

    @classmethod
    def of(cls, x: float | Scalar = 0.0, y: float | Scalar = 0.0, z: float | Scalar = 0.0) -> Vec3:
        """A vector from components — a literal if all are numbers, a graph if any is a ``Scalar``."""
        literal: list[float] = []
        for component in (x, y, z):
            if isinstance(component, Scalar):
                from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
                from fungeom.primitives.vec3.resolvers.components import ComponentVec3

                return ComponentVec3(x=as_scalar_resolver(x), y=as_scalar_resolver(y), z=as_scalar_resolver(z))
            literal.append(component)

        from fungeom.primitives.vec3.resolvers.literal import LiteralVec3
        from fungeom.primitives.vec3.value import as_vec3

        return LiteralVec3(value=as_vec3(literal))

    def scale(self, factor: float | Scalar) -> Vec3:
        """This vector multiplied by a (deferred) scalar."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.vec3.resolvers.scaled import ScaledVec3

        return ScaledVec3(vector=self, factor=as_scalar_resolver(factor))

    def negate(self) -> Vec3:
        """The opposite vector."""
        return self.scale(-1.0)

    def norm(self) -> Scalar:
        """The Euclidean length of this vector, as a deferred scalar."""
        from fungeom.primitives.vec3.resolvers.norm import Vec3Norm

        return Vec3Norm(vector=self)

    def normalized(self) -> Vec3:
        """The unit vector in this direction (Unresolvable if this is zero)."""
        from fungeom.primitives.vec3.resolvers.normalized import NormalizedVec3

        return NormalizedVec3(vector=self)

    def dot(self, other: Vec3) -> Scalar:
        """The dot product with ``other``, as a deferred scalar."""
        from fungeom.primitives.vec3.resolvers.dot import Vec3Dot

        return Vec3Dot(a=self, b=other)

    def cross(self, other: Vec3) -> Vec3:
        """The cross product with ``other``."""
        from fungeom.primitives.vec3.resolvers.cross import CrossVec3

        return CrossVec3(a=self, b=other)

    def project_onto(self, other: Vec3) -> Vec3:
        """This vector's component along ``other`` (Unresolvable if ``other`` is zero)."""
        from fungeom.primitives.vec3.resolvers.projected import ProjectedVec3

        return ProjectedVec3(a=self, onto=other)

    def reject_from(self, other: Vec3) -> Vec3:
        """This vector's component orthogonal to ``other`` (Unresolvable if ``other`` is zero)."""
        from fungeom.primitives.vec3.resolvers.projected import RejectedVec3

        return RejectedVec3(a=self, onto=other)

    def lerp(self, other: Vec3, t: float | Scalar) -> Vec3:
        """Linearly interpolate toward ``other`` (``t=0`` here, ``t=1`` there)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.vec3.resolvers.lerp import LerpVec3

        return LerpVec3(a=self, b=other, t=as_scalar_resolver(t))

    def __add__(self, other: Vec3) -> Vec3:
        from fungeom.primitives.vec3.resolvers.sum import SumVec3

        return SumVec3(a=self, b=other)

    def __sub__(self, other: Vec3) -> Vec3:
        from fungeom.primitives.vec3.resolvers.sum import SumVec3

        return SumVec3(a=self, b=other.negate())
