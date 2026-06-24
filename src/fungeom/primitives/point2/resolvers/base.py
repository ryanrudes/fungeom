"""The ``Point2`` interface and its combinators — the 2D sibling of ``Point3``.

Combinator methods construct sibling resolver types, which in turn import this base —
so those imports are deferred into the method bodies to keep module load acyclic.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolver import Resolver
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.frame2.value import WORLD_FRAME2, CoordinateFrame2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.vec2.resolvers.base import Vec2
from fungeom.primitives.vec2.resolvers.literal import vec2_resolver
from fungeom.primitives.vec2.value import Float2, as_vec2


class Point2(Resolver[Point2Value]):
    """A deferred 2D point — a position expressed in some coordinate frame.

    Construct with :meth:`at` (from coordinates — plain or deferred — in a frame),
    :meth:`in_frame`, :meth:`centroid`, or :meth:`affine`; compose with
    :meth:`translate`, :meth:`midpoint`, :meth:`lerp`, :meth:`displacement_to`
    (→ :class:`~fungeom.Vec2`), :meth:`distance_to` (→ :class:`~fungeom.Scalar`),
    :meth:`direction_to` (→ :class:`~fungeom.Direction2`), :meth:`transformed_by`,
    :meth:`reflect_across`.

    ``resolve()`` is *world-anchoring*: it returns a ``Point2.Value`` re-expressed in the
    world frame. A point whose frame is *detached* (not grounded to the world) is
    :class:`~fungeom.Unresolvable`, with the offending frame named in the reason.
    """

    type Value = Point2Value
    """The resolved value type — a position with the frame it lives in."""

    @classmethod
    def at(
        cls,
        x: float | Scalar,
        y: float | Scalar,
        frame: CoordinateFrame2 | Frame2 = WORLD_FRAME2,
    ) -> Point2:
        """A point at ``(x, y)`` in ``frame`` (the world frame by default).

        Coordinates may be plain numbers or deferred ``Scalar``s, and ``frame`` may be a
        :class:`CoordinateFrame2` value or a deferred :class:`Frame2`.
        """
        literal: list[float] = []
        for component in (x, y):
            if isinstance(component, Scalar):
                return cls.in_frame(Vec2.of(x, y), frame)
            literal.append(component)
        if isinstance(frame, Frame2):
            return cls.in_frame(Vec2.of(x, y), frame)

        from fungeom.primitives.point2.resolvers.located import LocatedPoint2

        return LocatedPoint2(point=Point2Value.of(literal[0], literal[1], frame))

    @classmethod
    def in_frame(cls, local: Vec2, frame: CoordinateFrame2 | Frame2 = WORLD_FRAME2) -> Point2:
        """A point at deferred ``local`` coordinates in a (deferred) ``frame``."""
        from fungeom.primitives.frame2.resolvers.known import as_frame2
        from fungeom.primitives.point2.resolvers.framed import FramedPoint2

        return FramedPoint2(local=local, frame=as_frame2(frame))

    @classmethod
    def centroid(cls, points: Iterable[Point2]) -> Point2:
        """The centroid of ``points`` (Unresolvable if there are none)."""
        from fungeom.primitives.point2.resolvers.centroid import Centroid2

        return Centroid2(points=tuple(points))

    @classmethod
    def affine(cls, points: Sequence[Point2], weights: Sequence[float | Scalar]) -> Point2:
        """A weighted combination of ``points`` (Unresolvable if weights total zero)."""
        from fungeom.primitives.point2.resolvers.affine import affine_combination2

        return affine_combination2(points, weights)

    def translate(self, offset: Vec2 | Float2 | ArrayLike) -> Point2:
        """Translate this point by a world-frame displacement."""
        from fungeom.primitives.point2.resolvers.translated import TranslatedPoint2

        resolver = offset if isinstance(offset, Vec2) else vec2_resolver(as_vec2(offset))
        return TranslatedPoint2(point=self, offset=resolver)

    def lerp(self, other: Point2, t: float | Scalar) -> Point2:
        """Linearly interpolate toward ``other`` (``t=0`` here, ``t=1`` there)."""
        from fungeom.primitives.point2.resolvers.lerp import Lerp2
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return Lerp2(a=self, b=other, t=as_scalar_resolver(t))

    def midpoint(self, other: Point2) -> Point2:
        """The point halfway between this point and ``other``."""
        return self.lerp(other, 0.5)

    def displacement_to(self, other: Point2) -> Vec2:
        """The world-frame vector from this point to ``other``."""
        from fungeom.primitives.point2.resolvers.displacement import DisplacementVec2

        return DisplacementVec2(start=self, end=other)

    def distance_to(self, other: Point2) -> Scalar:
        """The distance to ``other``, as a deferred scalar (norm of the displacement)."""
        return self.displacement_to(other).norm()

    def direction_to(self, other: Point2) -> Direction2:
        """The unit direction toward ``other`` (Unresolvable if the points coincide)."""
        from fungeom.primitives.direction2.resolvers.normalized import as_direction2

        return as_direction2(self.displacement_to(other))

    def transformed_by(self, transform: Transform2) -> Point2:
        """This point moved by a rigid ``transform`` — a motion in the world frame."""
        from fungeom.primitives.point2.resolvers.transformed import TransformedPoint2

        return TransformedPoint2(point=self, transform=transform)

    def reflect_across(self, center: Point2) -> Point2:
        """This point reflected through ``center`` (central symmetry: ``2·center − self``)."""
        from fungeom.primitives.point2.resolvers.reflected import ReflectedPoint2

        return ReflectedPoint2(point=self, center=center)
