"""``Point3Bundle`` — a point cloud: a keyed collection of positions.

The headline collection facade and the first nominal-axis field. Members are
``Point3`` resolvers, grounded (world-anchored) at *build* time exactly as a
``Point3Signal``'s samples are — so a point on a detached frame makes the whole
bundle :class:`~fungeom.Unresolvable` (construction is strict). ``at(key)`` bridges
back to the static ``Point3`` algebra, the way ``Signal.at(t)`` does; ``centroid``
folds over the *present* members (tolerant of absence, strict over op-failure).
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.base import Bundle
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


class Point3Bundle(Bundle[Point3Value]):
    """A deferred point cloud — a keyed, possibly-masked collection of positions.

    Construct with :meth:`of` (a list of points), :meth:`from_array` (a raw ``(N, 3)``
    coordinate array in a shared frame), or :meth:`from_map` (a mapping, optionally
    over a larger ``roster`` so the missing keys read as *absent* — an occluded
    marker set). Query with
    :meth:`at` (→ a rich ``Point3``), :meth:`present` / :meth:`count` (from the base),
    :meth:`where` (restrict to a subset), and fold with :meth:`centroid`.
    ``resolve()`` yields a ``BundleValue[Point3Value]`` of world-anchored positions.

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
        pts = tuple(points)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(pts)))
        return _GatheredPoint3Bundle(member_keys=member_keys, points=pts, roster=member_keys)

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
        pts = tuple(members[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredPoint3Bundle(member_keys=member_keys, points=pts, roster=full)

    def at(self, key: Hashable) -> Point3:
        """The position for ``key`` (→ ``Point3``); Unresolvable if absent or unknown."""
        return _Point3BundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable]) -> Point3Bundle:
        """The sub-cloud restricted to ``keys`` (roster and support both narrowed)."""
        return _WherePoint3Bundle(source=self, keep=tuple(keys))

    def centroid(self) -> Point3:
        """The centroid of the *present* members (→ ``Point3``); Unresolvable if none are."""
        return _BundleCentroid3(bundle=self)


@dataclass(frozen=True, eq=False)
class _GatheredPoint3Bundle(Point3Bundle):
    """Grounds each point member (the frame partiality) before building the collection."""

    member_keys: tuple[Hashable, ...]
    points: tuple[Point3, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[Point3Value]:
        if len(self.member_keys) != len(self.points):
            return Unresolvable(f"{len(self.points)} points for {len(self.member_keys)} keys")
        if len(set(self.member_keys)) != len(self.member_keys):
            return Unresolvable("duplicate keys in the bundle")
        members: dict[Hashable, Point3Value] = {}
        for key, point in zip(self.member_keys, self.points):
            decided = point.decide()
            if isinstance(decided, Unresolvable):
                return decided
            members[key] = decided.value
        return Resolvable(BundleValue(roster=self.roster, members=members))


@dataclass(frozen=True, eq=False)
class _WherePoint3Bundle(Point3Bundle):
    """The sub-cloud of ``source`` restricted to the ``keep`` keys."""

    source: Point3Bundle
    keep: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[Point3Value]:
        match self.source.decide():
            case Resolvable(collection):
                keep = set(self.keep)
                roster = tuple(key for key in collection.roster if key in keep)
                members = {key: value for key, value in collection.members.items() if key in keep}
                return Resolvable(BundleValue(roster=roster, members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _Point3BundleAt(Point3):
    """The member of ``bundle`` at ``key`` — bridges back to the static Point3 algebra."""

    bundle: Point3Bundle
    key: Hashable

    def _decide(self) -> Point3Decision:
        match self.bundle.decide():
            case Resolvable(collection):
                if self.key not in collection.roster:
                    return Unresolvable(f"key {self.key!r} is not in the bundle's roster")
                if not collection.present(self.key):
                    return Unresolvable(f"key {self.key!r} is absent from the bundle")
                return Resolvable(collection.at(self.key))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


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
