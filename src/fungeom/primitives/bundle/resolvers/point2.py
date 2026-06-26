"""``Point2Bundle`` — a planar point cloud: a keyed collection of 2D positions.

The 2D sibling of :class:`~fungeom.primitives.bundle.resolvers.point3.Point3Bundle`,
and the collection the :class:`~fungeom.Region2` rung consumes and produces: the markers
projected into a patch's plane (``hull``'s input) and a region's sampled corners/boundary
(``corners``/``sample``'s output) are both ``Point2Bundle``s. Members are ``Point2``
resolvers, grounded at *build* time exactly as a ``Point3Bundle``'s are — a point on a
detached 2D frame makes the whole bundle :class:`~fungeom.Unresolvable` (construction is
strict). ``at(key)`` bridges back to the static ``Point2`` algebra; ``centroid`` folds over
the *present* members.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass

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
from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.frame2.value import WORLD_FRAME2, CoordinateFrame2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.resolvers.base import Transform2


class Point2Bundle(Bundle[Point2Value]):
    """A deferred planar point cloud — a keyed, possibly-masked collection of 2D positions.

    Construct with :meth:`of` (a list of points), :meth:`from_array` (a raw ``(N, 2)``
    coordinate array in a shared 2D frame), or :meth:`from_map` (a mapping, optionally over
    a larger ``roster`` so the missing keys read as *absent*). Query with :meth:`at` (→ a
    rich ``Point2``), :meth:`present` / :meth:`count` / :meth:`support` (from the base),
    :meth:`where` (restrict to a subset), and fold with :meth:`centroid`. ``resolve()``
    yields a ``BundleValue[Point2Value]`` of world-anchored positions.

    Partiality has three layers: the bundle fails to *build* if any member is unresolvable
    (a detached frame) or the keys are malformed; a key may be *absent* (off the support);
    and a fold over no present members is ``Unresolvable``.
    """

    type Value = BundleValue[Point2Value]
    """The resolved value type — a keyed collection of world-anchored 2D positions."""

    @classmethod
    def of(cls, points: Sequence[Point2], keys: Sequence[Hashable] | None = None) -> Point2Bundle:
        """A cloud from ``points``, keyed by ``keys`` (or by position ``0..N-1``).

        Every point is present. Unresolvable to build if ``keys`` is given with a
        different length, if keys are duplicated, or if any point is.
        """
        members = tuple(points)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredPoint2Bundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_array(
        cls,
        coords: ArrayLike,
        keys: Sequence[Hashable] | None = None,
        frame: CoordinateFrame2 | Frame2 = WORLD_FRAME2,
    ) -> Point2Bundle:
        """A cloud from a raw ``(N, 2)`` coordinate array, all points in ``frame``.

        The natural input for a dense planar cloud. Keyed by ``keys`` or by position
        ``0..N-1``; every point is present (use :meth:`from_map` for an occluded set).
        """
        rows = np.asarray(coords, dtype=float).reshape(-1, 2)
        points = tuple(Point2.at(float(x), float(y), frame=frame) for x, y in rows)
        return cls.of(points, keys=keys)

    @classmethod
    def from_map(
        cls,
        members: Mapping[Hashable, Point2],
        roster: Sequence[Hashable] | None = None,
    ) -> Point2Bundle:
        """A cloud from a ``{key: point}`` mapping, optionally over a larger ``roster``.

        With a ``roster`` wider than the mapping, the unmapped keys are *absent*: they are
        in the roster but off the support.
        """
        member_keys = tuple(members)
        points = tuple(members[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredPoint2Bundle(member_keys=member_keys, members=points, roster=full)

    def at(self, key: Hashable) -> Point2:
        """The position for ``key`` (→ ``Point2``); Unresolvable if absent or unknown."""
        return _Point2BundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable] | Roster) -> Point2Bundle:
        """The sub-cloud restricted to ``keys`` (roster and support both narrowed)."""
        return _WherePoint2Bundle(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def relabel(self, mapping: RosterMap) -> Point2Bundle:
        """Re-key the cloud through ``mapping`` — the identity transfer of retargeting.

        Unmapped keys drop; the occlusion mask transfers. Unresolvable if the
        correspondence collapses two keys onto the same target.
        """
        return _RelabeledPoint2Bundle(source=self, mapping=mapping)

    def centroid(self) -> Point2:
        """The centroid of the *present* members (→ ``Point2``); Unresolvable if none are."""
        return _BundleCentroid2(bundle=self)

    def transformed_by(self, transform: Transform2) -> Point2Bundle:
        """Every present point moved by one rigid ``transform`` (a broadcast / map)."""
        return _TransformedPoint2Bundle(source=self, transform=transform)

    def distance_to(self, other: Point2Bundle) -> ScalarBundle:
        """The key-aligned distances from this cloud to ``other`` (→ ``ScalarBundle``)."""
        return _DistanceScalarBundle2(a=self, b=other)

    def map_scalar(self, func: Callable[[Point2], Scalar]) -> ScalarBundle:
        """Apply ``func`` to each present member (→ ``ScalarBundle``) — the open per-member escape hatch."""
        return _MappedScalarBundle2(source=self, func=func)

    def map_point(self, func: Callable[[Point2], Point2]) -> Point2Bundle:
        """Apply ``func`` to each present member (→ ``Point2Bundle``); the op's partiality flows."""
        return _MappedPoint2Bundle(source=self, func=func)

    def distances_to(self, point: Point2) -> ScalarBundle:
        """Each present member's distance to one ``point`` (a one-query broadcast → ``ScalarBundle``)."""
        return self.map_scalar(lambda member: member.distance_to(point))

    def closest_point_to(self, point: Point2) -> Point2:
        """The present member nearest ``point`` (→ ``Point2``); Unresolvable over an empty cloud."""
        return _ClosestPointInBundle2(cloud=self, query=point)

    def nearest_to(self, point: Point2) -> Roster:
        """The key of the present member nearest ``point``, as a singleton :class:`Roster`.

        Composes :meth:`distances_to` with :meth:`ScalarBundle.argmin` (empty → Unresolvable, ties →
        first in roster order); ``cloud.where(cloud.nearest_to(p))`` slices that marker out.
        """
        return self.distances_to(point).argmin()

    def bounds(self) -> Point2Bundle:
        """The axis-aligned bounding box as a ``{'min', 'max'}`` corner cloud (→ ``Point2Bundle``; Unresolvable if empty)."""
        return _Point2BundleBounds(source=self)


@dataclass(frozen=True, eq=False)
class _GatheredPoint2Bundle(Point2Bundle):
    """Grounds each point member (the frame partiality) before building the collection."""

    member_keys: tuple[Hashable, ...]
    members: tuple[Point2, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[Point2Value]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WherePoint2Bundle(Point2Bundle):
    """The sub-cloud of ``source`` restricted to the ``keep`` keys."""

    source: Point2Bundle
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> BundleDecision[Point2Value]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledPoint2Bundle(Point2Bundle):
    """The cloud ``source`` re-keyed through ``mapping`` (the retarget identity transfer)."""

    source: Point2Bundle
    mapping: RosterMap

    def _decide(self) -> BundleDecision[Point2Value]:
        return decide_relabeled(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _Point2BundleAt(Point2):
    """The member of ``bundle`` at ``key`` — bridges back to the static Point2 algebra."""

    bundle: Point2Bundle
    key: Hashable

    def _decide(self) -> Point2Decision:
        return decide_member_at(self.bundle, self.key)


@dataclass(frozen=True, eq=False)
class _BundleCentroid2(Point2):
    """The centroid of the present members of ``bundle`` (world-anchored)."""

    bundle: Point2Bundle

    def _decide(self) -> Point2Decision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("centroid of an empty bundle is undefined")
                mean = np.mean([point.coord for point in present], axis=0)
                return Resolvable(Point2Value(coord=mean, frame=WORLD_FRAME2))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _TransformedPoint2Bundle(Point2Bundle):
    """Every present point of ``source`` moved by one ``transform`` (a broadcast)."""

    source: Point2Bundle
    transform: Transform2

    def _decide(self) -> BundleDecision[Point2Value]:
        return decide_mapped(self.source, lambda key: self.source.at(key).transformed_by(self.transform))


@dataclass(frozen=True, eq=False)
class _DistanceScalarBundle2(ScalarBundle):
    """The key-aligned distances between two planar clouds — a cross-type lift to scalars."""

    a: Point2Bundle
    b: Point2Bundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key).distance_to(self.b.at(key)))


@dataclass(frozen=True, eq=False)
class _MappedScalarBundle2(ScalarBundle):
    """Each present member of ``source`` mapped through ``func`` to a scalar (the generic escape hatch)."""

    source: Point2Bundle
    func: Callable[[Point2], Scalar]

    def _decide(self) -> BundleDecision[float]:
        return decide_mapped(self.source, lambda key: self.func(self.source.at(key)))


@dataclass(frozen=True, eq=False)
class _MappedPoint2Bundle(Point2Bundle):
    """Each present member of ``source`` mapped through ``func`` to a point."""

    source: Point2Bundle
    func: Callable[[Point2], Point2]

    def _decide(self) -> BundleDecision[Point2Value]:
        return decide_mapped(self.source, lambda key: self.func(self.source.at(key)))


@dataclass(frozen=True, eq=False)
class _ClosestPointInBundle2(Point2):
    """The present member of ``cloud`` nearest the ``query`` point."""

    cloud: Point2Bundle
    query: Point2

    def _decide(self) -> Point2Decision:
        match self.cloud.decide(), self.query.decide():
            case (Resolvable(collection), Resolvable(query)):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("closest_point_to over an empty bundle is undefined")
                nearest = min(present, key=lambda member: float(np.sum((member.coord - query.coord) ** 2)))
                return Resolvable(Point2Value(coord=nearest.coord, frame=WORLD_FRAME2))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _Point2BundleBounds(Point2Bundle):
    """The axis-aligned bounding box of ``source`` as a ``{'min', 'max'}`` corner cloud."""

    source: Point2Bundle

    def _decide(self) -> BundleDecision[Point2Value]:
        match self.source.decide():
            case Resolvable(collection):
                present = [collection.members[key].coord for key in collection.support()]
                if not present:
                    return Unresolvable("bounds of an empty bundle is undefined")
                stacked = np.array(present)
                members: dict[Hashable, Point2Value] = {
                    "min": Point2Value(coord=stacked.min(axis=0), frame=WORLD_FRAME2),
                    "max": Point2Value(coord=stacked.max(axis=0), frame=WORLD_FRAME2),
                }
                return Resolvable(BundleValue(roster=("min", "max"), members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
