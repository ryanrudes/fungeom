"""The ``Point3`` interface and its combinators.

Combinator methods construct sibling resolver types, which in turn import this
base — so those imports are deferred into the method bodies to keep module load
acyclic. (Vector types live in a lower layer and are imported normally.)
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Sequence

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolver import Resolver
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.point3.coercion import SupportsPoint3, _as_point3, _as_point3s
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.resolvers.literal import vec3_resolver
from fungeom.primitives.vec3.value import Float3, as_vec3


class Point3(Resolver[Point3Value]):
    """A deferred 3D point — a position expressed in some coordinate frame.

    Construct with :meth:`at` (from coordinates — plain or deferred — in a frame),
    :meth:`in_frame`, :meth:`centroid`, or :meth:`affine`; compose with
    :meth:`translate`, :meth:`midpoint`, :meth:`lerp`, :meth:`displacement_to`
    (→ :class:`~fungeom.Vec3`), :meth:`distance_to`
    (→ :class:`~fungeom.Scalar`), :meth:`direction_to`
    (→ :class:`~fungeom.Direction3`), :meth:`transformed_by`, :meth:`reflect_across`.

    ``resolve()`` is *world-anchoring*: it returns a ``Point3.Value`` re-expressed
    in the world frame. A point whose frame is *detached* (not grounded to the
    world) is :class:`~fungeom.Unresolvable`, with the offending frame
    named in the reason — see :meth:`decide`.
    """

    type Value = Point3Value
    """The resolved value type — a position with the frame it lives in."""

    @classmethod
    def at(
        cls,
        x: float | Scalar,
        y: float | Scalar,
        z: float | Scalar,
        frame: CoordinateFrame | Frame = WORLD_FRAME,
    ) -> Point3:
        """A point at ``(x, y, z)`` in ``frame`` (the world frame by default).

        Coordinates may be plain numbers or deferred ``Scalar``s, and ``frame``
        may be a :class:`CoordinateFrame` value or a deferred :class:`Frame`. The
        all-numbers / value-frame case is a literal leaf; anything deferred
        builds the corresponding graph.
        """
        literal: list[float] = []
        for component in (x, y, z):
            if isinstance(component, Scalar):
                return cls.in_frame(Vec3.of(x, y, z), frame)
            literal.append(component)
        if isinstance(frame, Frame):
            return cls.in_frame(Vec3.of(x, y, z), frame)

        from fungeom.primitives.point3.resolvers.located import LocatedPoint3

        return LocatedPoint3(point=Point3Value.of(literal[0], literal[1], literal[2], frame))

    @classmethod
    def in_frame(cls, local: Vec3, frame: CoordinateFrame | Frame = WORLD_FRAME) -> Point3:
        """A point at deferred ``local`` coordinates in a (deferred) ``frame``."""
        from fungeom.primitives.frame.resolvers.known import as_frame
        from fungeom.primitives.point3.resolvers.framed import FramedPoint3

        return FramedPoint3(local=local, frame=as_frame(frame))

    @classmethod
    def centroid(cls, points: Iterable[Point3 | SupportsPoint3]) -> Point3:
        """The centroid of ``points`` (Unresolvable if there are none)."""
        from fungeom.primitives.point3.resolvers.centroid import Centroid3

        return Centroid3(points=tuple(_as_point3s(points)))

    @classmethod
    def affine(cls, points: Sequence[Point3 | SupportsPoint3], weights: Sequence[float | Scalar]) -> Point3:
        """A weighted combination of ``points`` (Unresolvable if weights total zero)."""
        from fungeom.primitives.point3.resolvers.affine import affine_combination

        return affine_combination(_as_point3s(points), weights)

    @classmethod
    def free(cls, identity: Hashable) -> Point3:
        """A late-bound point identified by ``identity`` — ``Unresolvable`` until bound.

        The unknown as a first-class leaf: a ``Point3`` that has no position yet, carrying
        an opaque :class:`~collections.abc.Hashable` ``identity``. It composes through the
        whole algebra like any other point (``Point3Bundle.of([Point3.free(a), …])`` has a
        ``fit_plane``, that has a ``Face``, …); :meth:`~fungeom.core.resolver.Resolver.bind`
        / :meth:`~fungeom.core.resolver.Resolver.resolve_in` fill it in from an
        ``identity -> resolver`` environment. Lets a construction be authored as data over
        late-bound references (e.g. markers) instead of an imperative callable.
        """
        from fungeom.primitives.point3.resolvers.free import FreePoint3

        return FreePoint3(identity=identity)

    def translate(self, offset: Vec3 | Float3 | ArrayLike) -> Point3:
        """Translate this point by a world-frame displacement."""
        from fungeom.primitives.point3.resolvers.translated import TranslatedPoint3

        resolver = offset if isinstance(offset, Vec3) else vec3_resolver(as_vec3(offset))
        return TranslatedPoint3(point=self, offset=resolver)

    def lerp(self, other: Point3 | SupportsPoint3, t: float | Scalar) -> Point3:
        """Linearly interpolate toward ``other`` (``t=0`` here, ``t=1`` there)."""
        from fungeom.primitives.point3.resolvers.lerp import Lerp3
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return Lerp3(a=self, b=_as_point3(other), t=as_scalar_resolver(t))

    def midpoint(self, other: Point3 | SupportsPoint3) -> Point3:
        """The point halfway between this point and ``other``."""
        return self.lerp(other, 0.5)

    def displacement_to(self, other: Point3 | SupportsPoint3) -> Vec3:
        """The world-frame vector from this point to ``other``."""
        from fungeom.primitives.point3.resolvers.displacement import DisplacementVec3

        return DisplacementVec3(start=self, end=_as_point3(other))

    def distance_to(self, other: Point3 | SupportsPoint3) -> Scalar:
        """The distance to ``other``, as a deferred scalar (norm of the displacement)."""
        return self.displacement_to(other).norm()

    def direction_to(self, other: Point3 | SupportsPoint3) -> Direction3:
        """The unit direction toward ``other`` (Unresolvable if the points coincide)."""
        from fungeom.primitives.direction3.resolvers.normalized import as_direction

        return as_direction(self.displacement_to(other))

    def transformed_by(self, transform: Transform) -> Point3:
        """This point moved by a rigid ``transform`` — a motion in the world frame."""
        from fungeom.primitives.point3.resolvers.transformed import TransformedPoint3

        return TransformedPoint3(point=self, transform=transform)

    def reflect_across(self, center: Point3 | SupportsPoint3) -> Point3:
        """This point reflected through ``center`` (central symmetry: ``2·center − self``)."""
        from fungeom.primitives.point3.resolvers.reflected import ReflectedPoint3

        return ReflectedPoint3(point=self, center=_as_point3(center))

    def coordinates_in(self, frame: CoordinateFrame | Frame) -> Vec3:
        """This point's coordinates expressed in ``frame`` (→ ``Vec3``) — the inverse of :meth:`in_frame`.

        Where :meth:`in_frame` *builds* a point from a local coordinate vector in a frame, this
        *reads* that vector back: the ``(x, y, z)`` of this (world-anchored) point measured in
        ``frame``. ``Unresolvable`` if ``frame`` is ungrounded — a detached frame has no
        world-relative coordinates.
        """
        from fungeom.primitives.frame.resolvers.known import as_frame
        from fungeom.primitives.point3.resolvers.local_coordinates import LocalCoordinates3

        return LocalCoordinates3(point=self, frame=as_frame(frame))
