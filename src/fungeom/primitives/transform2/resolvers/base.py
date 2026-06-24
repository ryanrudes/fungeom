"""The ``Transform2`` interface and its algebra — the 2D sibling of ``Transform``."""

from __future__ import annotations

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolver import Resolver
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.value import RigidTransform2
from fungeom.primitives.vec2.resolvers.base import Vec2


class Transform2(Resolver[RigidTransform2]):
    """A deferred rigid 2D transform — a rotation plus a translation (an element of SE(2)).

    Construct with :meth:`identity`, :meth:`translation`, :meth:`rotation` (an angle —
    no axis is needed in 2D), or :meth:`known` (wrapping a
    :class:`~fungeom.RigidTransform2` value); compose with ``@`` (:meth:`compose`),
    :meth:`inverse`; apply to geometry with :meth:`transform_vector` /
    :meth:`transform_direction`, and decompose with :meth:`translation_part` /
    :meth:`rotation_part` / :meth:`angle`. ``resolve()`` yields a
    :class:`~fungeom.RigidTransform2` (``Transform2.Value``).

    A transform built from a deferred vector or scalar inherits its resolvability; a 2D
    rotation is always well-defined (there is no zero-axis case as in SE(3)).
    """

    type Value = RigidTransform2
    """The resolved value type — a :class:`RigidTransform2`."""

    @classmethod
    def identity(cls) -> Transform2:
        """The identity transform."""
        from fungeom.primitives.transform2.resolvers.literal import LiteralTransform2

        return LiteralTransform2(value=RigidTransform2.identity())

    @classmethod
    def known(cls, value: RigidTransform2) -> Transform2:
        """Wrap an already-known :class:`RigidTransform2` value."""
        from fungeom.primitives.transform2.resolvers.literal import LiteralTransform2

        return LiteralTransform2(value=value)

    @classmethod
    def translation(cls, vector: Vec2 | ArrayLike) -> Transform2:
        """A pure-translation transform from a vector (deferred, or raw components)."""
        from fungeom.primitives.transform2.resolvers.translation import TranslationTransform2
        from fungeom.primitives.vec2.resolvers.literal import LiteralVec2
        from fungeom.primitives.vec2.value import as_vec2

        resolver = vector if isinstance(vector, Vec2) else LiteralVec2(value=as_vec2(vector))
        return TranslationTransform2(vector=resolver)

    @classmethod
    def rotation(cls, angle: float | Scalar) -> Transform2:
        """A rotation of ``angle`` radians (counter-clockwise) about the origin."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.transform2.resolvers.rotation import RotationTransform2

        return RotationTransform2(radians=as_scalar_resolver(angle))

    def compose(self, other: Transform2) -> Transform2:
        """``self ∘ other`` — apply ``other`` first, then ``self``."""
        from fungeom.primitives.transform2.resolvers.composed import ComposedTransform2

        return ComposedTransform2(a=self, b=other)

    def __matmul__(self, other: Transform2) -> Transform2:
        return self.compose(other)

    def inverse(self) -> Transform2:
        """The inverse transform."""
        from fungeom.primitives.transform2.resolvers.inverse import InverseTransform2

        return InverseTransform2(transform=self)

    def slerp(self, other: Transform2, t: float | Scalar) -> Transform2:
        """Smoothly interpolate toward ``other`` (rotation along the shortest arc, translation linearly)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.transform2.resolvers.slerp import SlerpTransform2

        return SlerpTransform2(a=self, b=other, t=as_scalar_resolver(t))

    def transform_vector(self, vector: Vec2) -> Vec2:
        """Apply this transform to a free ``vector`` — rotated only, not translated."""
        from fungeom.primitives.transform2.resolvers.applied_vector import TransformedVec2

        return TransformedVec2(transform=self, vector=vector)

    def transform_direction(self, direction: Direction2) -> Direction2:
        """Apply this transform's rotation to a ``direction`` (the result stays unit length)."""
        from fungeom.primitives.transform2.resolvers.applied_direction import TransformedDirection2

        return TransformedDirection2(transform=self, direction=direction)

    def translation_part(self) -> Vec2:
        """This transform's translation component, as a vector."""
        from fungeom.primitives.transform2.resolvers.translation_part import TranslationPart2

        return TranslationPart2(transform=self)

    def rotation_part(self) -> Transform2:
        """This transform with its translation dropped — the rotation alone."""
        from fungeom.primitives.transform2.resolvers.rotation_part import RotationPart2

        return RotationPart2(transform=self)

    def angle(self) -> Scalar:
        """This transform's rotation angle (radians), in ``(-π, π]`` (→ ``Scalar``)."""
        from fungeom.primitives.transform2.resolvers.angle import Transform2Angle

        return Transform2Angle(transform=self)
