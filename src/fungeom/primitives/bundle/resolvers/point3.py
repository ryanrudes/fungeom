"""``Point3Bundle`` — a point cloud: a keyed collection of positions.

The headline collection facade and the first nominal-axis field. Members are
``Point3`` resolvers, grounded (world-anchored) at *build* time exactly as a
``Point3Signal``'s samples are — so a point on a detached frame makes the whole
bundle :class:`~fungeom.Unresolvable` (construction is strict). ``at(key)`` bridges
back to the static ``Point3`` algebra, the way ``Signal.at(t)`` does; ``centroid``
folds over the *present* members (tolerant of absence, strict over op-failure).
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import overload

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.base import (
    Bundle,
    decide_gathered,
    decide_mapped,
    decide_member_at,
    decide_relabeled,
    decide_where,
    decide_zipped,
)
from fungeom.primitives.bundle.resolvers.point2 import Point2Bundle
from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle
from fungeom.primitives.bundle.resolvers.transform import TransformBundle
from fungeom.primitives.bundle.resolvers.vec3 import Vec3Bundle
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.value import Float3


class Point3Bundle(Bundle[Point3Value]):
    """A deferred point cloud — a keyed, possibly-masked collection of positions.

    Construct with :meth:`of` (a list of points), :meth:`from_array` (a raw ``(N, 3)``
    coordinate array in a shared frame), or :meth:`from_map` (a mapping, optionally
    over a larger ``roster`` so the missing keys read as *absent* — an occluded
    marker set). Query with :meth:`at` (→ a rich ``Point3``), :meth:`present` /
    :meth:`count` (from the base), :meth:`where` (restrict to a subset), and fold with
    :meth:`centroid`. ``resolve()`` yields a ``BundleValue[Point3Value]`` of
    world-anchored positions.

    Partiality has three layers: the bundle fails to *build* if any member is
    unresolvable (a detached frame) or the keys are malformed; a key may be *absent*
    (off the support); and a fold over no present members is ``Unresolvable``.
    """

    type Value = BundleValue[Point3Value]
    """The resolved value type — a keyed collection of world-anchored positions."""

    @classmethod
    def of(cls, points: Sequence[Point3], keys: Sequence[Hashable] | None = None) -> Point3Bundle:
        """A cloud from ``points``, keyed by ``keys`` (or by position ``0..N-1``).

        Every point is present. Unresolvable to build if ``keys`` is given with a
        different length, if keys are duplicated, or if any point is.
        """
        members = tuple(points)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredPoint3Bundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_array(
        cls,
        coords: ArrayLike,
        keys: Sequence[Hashable] | None = None,
        frame: CoordinateFrame | Frame = WORLD_FRAME,
    ) -> Point3Bundle:
        """A cloud from a raw ``(N, 3)`` coordinate array, all points in ``frame``.

        The natural input for a dense point cloud. Keyed by ``keys`` or by position
        ``0..N-1``; every point is present (use :meth:`from_map` for an occluded set).
        """
        rows = np.asarray(coords, dtype=float).reshape(-1, 3)
        points = tuple(Point3.at(float(x), float(y), float(z), frame=frame) for x, y, z in rows)
        return cls.of(points, keys=keys)

    @classmethod
    def from_map(
        cls,
        members: Mapping[Hashable, Point3],
        roster: Sequence[Hashable] | None = None,
    ) -> Point3Bundle:
        """A cloud from a ``{key: point}`` mapping, optionally over a larger ``roster``.

        With a ``roster`` wider than the mapping, the unmapped keys are *absent*
        (the occluded-marker case): they are in the roster but off the support.
        """
        member_keys = tuple(members)
        points = tuple(members[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredPoint3Bundle(member_keys=member_keys, members=points, roster=full)

    def at(self, key: Hashable) -> Point3:
        """The position for ``key`` (→ ``Point3``); Unresolvable if absent or unknown."""
        return _Point3BundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable] | Roster) -> Point3Bundle:
        """The sub-cloud restricted to ``keys`` (roster and support both narrowed)."""
        return _WherePoint3Bundle(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def relabel(self, mapping: RosterMap) -> Point3Bundle:
        """Re-key the cloud through ``mapping`` — the identity transfer of retargeting.

        A cloud keyed by *source* entities (skeleton-A markers) becomes one keyed by
        *target* entities (skeleton-B joints), each position carried across unchanged.
        Unmapped keys drop; the occlusion mask transfers. Unresolvable if the
        correspondence collapses two keys onto the same target.
        """
        return _RelabeledPoint3Bundle(source=self, mapping=mapping)

    def centroid(self) -> Point3:
        """The centroid of the *present* members (→ ``Point3``); Unresolvable if none are."""
        return _BundleCentroid3(bundle=self)

    def fit_plane(self, *, tolerance: float = 1e-6) -> Plane:
        """The least-squares plane through the present points (→ ``Plane``, a numeric PCA fit).

        Unresolvable with fewer than three present points, or when the cloud has no unique
        normal direction (near-collinear or isotropic) at ``tolerance`` (a relative
        singular-value-gap test). The fitted normal's sign is arbitrary — orient it with
        :meth:`Plane.facing`.
        """
        from fungeom.primitives.bundle.resolvers.fit import FittedPlane

        return FittedPlane(cloud=self, tolerance=tolerance)

    def fit_line(self, *, tolerance: float = 1e-6) -> Line:
        """The least-squares line through the present points (→ ``Line``, a numeric PCA fit).

        Unresolvable with fewer than two present points, or when the cloud has no dominant
        direction (isotropic) at ``tolerance`` (a relative singular-value-gap test). The
        fitted direction's sign is arbitrary — orient it with :meth:`Line.direction_along`.
        """
        from fungeom.primitives.bundle.resolvers.fit import FittedLine

        return FittedLine(cloud=self, tolerance=tolerance)

    @overload
    def transformed_by(self, transform: Transform) -> Point3Bundle: ...
    @overload
    def transformed_by(self, transform: TransformBundle) -> Point3Bundle: ...
    def transformed_by(self, transform: Transform | TransformBundle) -> Point3Bundle:
        """Move the cloud by ``transform`` — one shared rigid motion, or a *per-key* one.

        A single ``Transform`` is broadcast over every present point; a ``TransformBundle`` is
        applied **key by key** (each marker moved by its same-key pose, on the key intersection) —
        the modeled-marker path, where each marker is rigidly attached to its own joint.
        """
        if isinstance(transform, TransformBundle):
            return _PerKeyTransformedPoint3Bundle(source=self, transforms=transform)
        return _TransformedPoint3Bundle(source=self, transform=transform)

    def in_frame(self, plane: Plane) -> Point2Bundle:
        """Flatten every present point into ``plane``'s 2D chart (→ ``Point2Bundle``).

        The broadcast of :meth:`Plane.to_local` — the markers-into-a-patch-plane step that
        feeds ``Region2.hull``. Absent keys stay absent; the occlusion mask carries through.
        """
        return _InFramePoint2Bundle(source=self, plane=plane)

    def displacement_to(self, other: Point3Bundle) -> Vec3Bundle:
        """The key-aligned vectors from this cloud to ``other`` (→ ``Vec3Bundle``)."""
        return _DisplacementVec3Bundle(a=self, b=other)

    def distance_to(self, other: Point3Bundle) -> ScalarBundle:
        """The key-aligned distances from this cloud to ``other`` (→ ``ScalarBundle``)."""
        return _DistanceScalarBundle(a=self, b=other)

    def map_scalar(self, func: Callable[[Point3], Scalar]) -> ScalarBundle:
        """Apply ``func`` to each present member (→ ``ScalarBundle``) — the open per-member escape hatch."""
        return _MappedScalarBundle(source=self, func=func)

    def map_point(self, func: Callable[[Point3], Point3]) -> Point3Bundle:
        """Apply ``func`` to each present member (→ ``Point3Bundle``)."""
        return _MappedPoint3Bundle(source=self, func=func)

    def map_vec3(self, func: Callable[[Point3], Vec3]) -> Vec3Bundle:
        """Apply ``func`` to each present member (→ ``Vec3Bundle``)."""
        return _MappedVec3Bundle(source=self, func=func)

    def distances_to(self, point: Point3) -> ScalarBundle:
        """Each present member's distance to one ``point`` (a one-query broadcast → ``ScalarBundle``)."""
        return self.map_scalar(lambda member: member.distance_to(point))

    def closest_point_to(self, point: Point3) -> Point3:
        """The present member nearest ``point`` (→ ``Point3``); Unresolvable over an empty cloud."""
        return _ClosestPointInBundle(cloud=self, query=point)

    def nearest_to(self, point: Point3) -> Roster:
        """The key of the present member nearest ``point``, as a singleton :class:`Roster`.

        Composes :meth:`distances_to` with :meth:`ScalarBundle.argmin`; resolver-shaped (empty →
        Unresolvable), ties → first in roster order. ``cloud.where(cloud.nearest_to(p))`` slices it.
        """
        return self.distances_to(point).argmin()

    def bounds(self) -> Point3Bundle:
        """The axis-aligned bounding box as a ``{'min', 'max'}`` corner cloud (→ ``Point3Bundle``; Unresolvable if empty)."""
        return _Point3BundleBounds(source=self)


@dataclass(frozen=True, eq=False)
class _GatheredPoint3Bundle(Point3Bundle):
    """Grounds each point member (the frame partiality) before building the collection."""

    member_keys: tuple[Hashable, ...]
    members: tuple[Point3, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WherePoint3Bundle(Point3Bundle):
    """The sub-cloud of ``source`` restricted to the ``keep`` keys."""

    source: Point3Bundle
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledPoint3Bundle(Point3Bundle):
    """The cloud ``source`` re-keyed through ``mapping`` (the retarget identity transfer)."""

    source: Point3Bundle
    mapping: RosterMap

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_relabeled(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _Point3BundleAt(Point3):
    """The member of ``bundle`` at ``key`` — bridges back to the static Point3 algebra."""

    bundle: Point3Bundle
    key: Hashable

    def _decide(self) -> Point3Decision:
        return decide_member_at(self.bundle, self.key)


@dataclass(frozen=True, eq=False)
class _BundleCentroid3(Point3):
    """The centroid of the present members of ``bundle`` (world-anchored)."""

    bundle: Point3Bundle

    def _decide(self) -> Point3Decision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("centroid of an empty bundle is undefined")
                mean = np.mean([point.coord for point in present], axis=0)
                return Resolvable(Point3Value(coord=mean, frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _TransformedPoint3Bundle(Point3Bundle):
    """Every present point of ``source`` moved by one ``transform`` (a broadcast)."""

    source: Point3Bundle
    transform: Transform

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_mapped(self.source, lambda key: self.source.at(key).transformed_by(self.transform))


@dataclass(frozen=True, eq=False)
class _PerKeyTransformedPoint3Bundle(Point3Bundle):
    """Each present point moved by its same-key pose — the per-joint (modeled-marker) transfer."""

    source: Point3Bundle
    transforms: TransformBundle

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_zipped(
            self.source, self.transforms, lambda key: self.source.at(key).transformed_by(self.transforms.at(key))
        )


@dataclass(frozen=True, eq=False)
class _InFramePoint2Bundle(Point2Bundle):
    """Every present point of ``source`` flattened into ``plane``'s chart — a cross-type lift to 2D."""

    source: Point3Bundle
    plane: Plane

    def _decide(self) -> BundleDecision[Point2Value]:
        return decide_mapped(self.source, lambda key: self.plane.to_local(self.source.at(key)))


@dataclass(frozen=True, eq=False)
class _DisplacementVec3Bundle(Vec3Bundle):
    """The key-aligned displacements between two point clouds — a cross-type lift to vectors."""

    a: Point3Bundle
    b: Point3Bundle

    def _decide(self) -> BundleDecision[Float3]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key).displacement_to(self.b.at(key)))


@dataclass(frozen=True, eq=False)
class _DistanceScalarBundle(ScalarBundle):
    """The key-aligned distances between two point clouds — a cross-type lift to scalars."""

    a: Point3Bundle
    b: Point3Bundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key).distance_to(self.b.at(key)))


@dataclass(frozen=True, eq=False)
class _MappedScalarBundle(ScalarBundle):
    """Each present member of ``source`` mapped through ``func`` to a scalar (the generic escape hatch)."""

    source: Point3Bundle
    func: Callable[[Point3], Scalar]

    def _decide(self) -> BundleDecision[float]:
        return decide_mapped(self.source, lambda key: self.func(self.source.at(key)))


@dataclass(frozen=True, eq=False)
class _MappedPoint3Bundle(Point3Bundle):
    """Each present member of ``source`` mapped through ``func`` to a point."""

    source: Point3Bundle
    func: Callable[[Point3], Point3]

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_mapped(self.source, lambda key: self.func(self.source.at(key)))


@dataclass(frozen=True, eq=False)
class _MappedVec3Bundle(Vec3Bundle):
    """Each present member of ``source`` mapped through ``func`` to a vector."""

    source: Point3Bundle
    func: Callable[[Point3], Vec3]

    def _decide(self) -> BundleDecision[Float3]:
        return decide_mapped(self.source, lambda key: self.func(self.source.at(key)))


@dataclass(frozen=True, eq=False)
class _ClosestPointInBundle(Point3):
    """The present member of ``cloud`` nearest the ``query`` point."""

    cloud: Point3Bundle
    query: Point3

    def _decide(self) -> Point3Decision:
        match self.cloud.decide(), self.query.decide():
            case (Resolvable(collection), Resolvable(query)):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("closest_point_to over an empty bundle is undefined")
                nearest = min(present, key=lambda member: float(np.sum((member.coord - query.coord) ** 2)))
                return Resolvable(Point3Value(coord=nearest.coord, frame=WORLD_FRAME))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _Point3BundleBounds(Point3Bundle):
    """The axis-aligned bounding box of ``source`` as a ``{'min', 'max'}`` corner cloud."""

    source: Point3Bundle

    def _decide(self) -> BundleDecision[Point3Value]:
        match self.source.decide():
            case Resolvable(collection):
                present = [collection.members[key].coord for key in collection.support()]
                if not present:
                    return Unresolvable("bounds of an empty bundle is undefined")
                stacked = np.array(present)
                members: dict[Hashable, Point3Value] = {
                    "min": Point3Value(coord=stacked.min(axis=0), frame=WORLD_FRAME),
                    "max": Point3Value(coord=stacked.max(axis=0), frame=WORLD_FRAME),
                }
                return Resolvable(BundleValue(roster=("min", "max"), members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
