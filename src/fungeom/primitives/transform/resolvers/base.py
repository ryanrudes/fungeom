"""The ``Transform`` interface and its algebra."""

from __future__ import annotations

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolver import Resolver
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.value import RigidTransform
from fungeom.primitives.vec3.resolvers.base import Vec3


class Transform(Resolver[RigidTransform]):
    """A deferred rigid transform — a rotation plus a translation (an element of SE(3)).

    Construct with :meth:`identity`, :meth:`translation`, :meth:`rotation`, or
    :meth:`known` (wrapping a :class:`~fungeom.RigidTransform` value);
    compose with ``@`` (:meth:`compose`), :meth:`inverse`, :meth:`slerp`; apply
    to geometry with :meth:`transform_vector` / :meth:`transform_direction`, and
    decompose with :meth:`translation_part` / :meth:`rotation_part`.
    ``resolve()`` yields a :class:`~fungeom.RigidTransform`
    (``Transform.Value``), which applies to points and vectors.

    A transform built from a deferred vector or scalar inherits its
    resolvability; :meth:`rotation` about the zero axis is
    :class:`~fungeom.Unresolvable`.
    """

    type Value = RigidTransform
    """The resolved value type — a :class:`RigidTransform`."""

    @classmethod
    def identity(cls) -> Transform:
        """The identity transform."""
        from fungeom.primitives.transform.resolvers.literal import LiteralTransform

        return LiteralTransform(value=RigidTransform.identity())

    @classmethod
    def known(cls, value: RigidTransform) -> Transform:
        """Wrap an already-known :class:`RigidTransform` value."""
        from fungeom.primitives.transform.resolvers.literal import LiteralTransform

        return LiteralTransform(value=value)

    @classmethod
    def translation(cls, vector: Vec3 | ArrayLike) -> Transform:
        """A pure-translation transform from a vector (deferred, or raw components)."""
        from fungeom.primitives.transform.resolvers.translation import TranslationTransform
        from fungeom.primitives.vec3.resolvers.literal import vec3_resolver
        from fungeom.primitives.vec3.value import as_vec3

        resolver = vector if isinstance(vector, Vec3) else vec3_resolver(as_vec3(vector))
        return TranslationTransform(vector=resolver)

    @classmethod
    def rotation(cls, axis: Vec3 | Direction3, angle: float | Scalar) -> Transform:
        """A rotation of ``angle`` radians about ``axis`` (Unresolvable about the zero axis).

        ``axis`` may be a vector or a :class:`Direction3`.
        """
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.transform.resolvers.axis_angle import AxisAngleTransform

        axis_vector = axis.as_vector() if isinstance(axis, Direction3) else axis
        return AxisAngleTransform(axis=axis_vector, angle=as_scalar_resolver(angle))

    def compose(self, other: Transform) -> Transform:
        """``self ∘ other`` — apply ``other`` first, then ``self``."""
        from fungeom.primitives.transform.resolvers.composed import ComposedTransform

        return ComposedTransform(a=self, b=other)

    def __matmul__(self, other: Transform) -> Transform:
        return self.compose(other)

    def inverse(self) -> Transform:
        """The inverse transform."""
        from fungeom.primitives.transform.resolvers.inverse import InverseTransform

        return InverseTransform(transform=self)

    def slerp(self, other: Transform, t: float | Scalar) -> Transform:
        """Smoothly interpolate toward ``other`` (slerp rotation, lerp translation)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.transform.resolvers.slerp import SlerpTransform

        return SlerpTransform(a=self, b=other, t=as_scalar_resolver(t))

    def transform_vector(self, vector: Vec3) -> Vec3:
        """Apply this transform to a free ``vector`` — rotated only, not translated."""
        from fungeom.primitives.transform.resolvers.applied_vector import TransformedVec3

        return TransformedVec3(transform=self, vector=vector)

    def transform_direction(self, direction: Direction3) -> Direction3:
        """Apply this transform's rotation to a ``direction`` (the result stays unit length)."""
        from fungeom.primitives.transform.resolvers.applied_direction import TransformedDirection3

        return TransformedDirection3(transform=self, direction=direction)

    def translation_part(self) -> Vec3:
        """This transform's translation component, as a vector."""
        from fungeom.primitives.transform.resolvers.translation_part import TranslationPart

        return TranslationPart(transform=self)

    def rotation_part(self) -> Transform:
        """This transform with its translation dropped — the rotation alone."""
        from fungeom.primitives.transform.resolvers.rotation_part import RotationPart

        return RotationPart(transform=self)
