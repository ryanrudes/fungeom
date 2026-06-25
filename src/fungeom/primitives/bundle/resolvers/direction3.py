"""``Direction3Bundle`` — a keyed collection of unit directions."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.base import (
    Bundle,
    decide_gathered,
    decide_member_at,
    decide_relabeled,
    decide_where,
)
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.resolvers.base import RosterMap


class Direction3Bundle(Bundle[Direction3Value]):
    """A deferred, keyed, possibly-masked collection of unit directions.

    Construct with :meth:`of`, :meth:`from_array` (a raw ``(N, 3)`` array, each row
    normalized — a zero row makes that member, and so the bundle, Unresolvable), or
    :meth:`from_map`; query with :meth:`at` (→ ``Direction3``), :meth:`present` /
    :meth:`count`, :meth:`where`, and fold with :meth:`mean` (→ ``Direction3``).
    """

    type Value = BundleValue[Direction3Value]
    """The resolved value type — a keyed collection of unit directions."""

    @classmethod
    def of(cls, directions: Sequence[Direction3], keys: Sequence[Hashable] | None = None) -> Direction3Bundle:
        """A bundle from ``directions``, keyed by ``keys`` (or by position ``0..N-1``)."""
        members = tuple(directions)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredDirection3Bundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_array(cls, directions: ArrayLike, keys: Sequence[Hashable] | None = None) -> Direction3Bundle:
        """A bundle from a raw ``(N, 3)`` array (each row normalized); every key present."""
        rows = np.asarray(directions, dtype=float).reshape(-1, 3)
        return cls.of(tuple(Direction3.of(float(x), float(y), float(z)) for x, y, z in rows), keys=keys)

    @classmethod
    def from_map(
        cls,
        directions: Mapping[Hashable, Direction3],
        roster: Sequence[Hashable] | None = None,
    ) -> Direction3Bundle:
        """A bundle from a ``{key: direction}`` mapping, optionally over a larger ``roster``."""
        member_keys = tuple(directions)
        members = tuple(directions[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredDirection3Bundle(member_keys=member_keys, members=members, roster=full)

    def at(self, key: Hashable) -> Direction3:
        """The direction for ``key`` (→ ``Direction3``); Unresolvable if absent or unknown."""
        return _Direction3BundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable] | Roster) -> Direction3Bundle:
        """The sub-bundle restricted to ``keys``."""
        return _WhereDirection3Bundle(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def relabel(self, mapping: RosterMap) -> Direction3Bundle:
        """Rename keys through ``mapping`` (Unresolvable if it collapses keys onto one target)."""
        return _RelabeledDirection3Bundle(source=self, mapping=mapping)

    def mean(self) -> Direction3:
        """The mean direction of the present members (normalize their sum, → ``Direction3``).

        Unresolvable if there are no present members, or if they cancel to the zero
        vector (e.g. exactly antipodal) — a sum with no direction has no mean.
        """
        return _Direction3BundleMean(bundle=self)


@dataclass(frozen=True, eq=False)
class _GatheredDirection3Bundle(Direction3Bundle):
    member_keys: tuple[Hashable, ...]
    members: tuple[Direction3, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[Direction3Value]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WhereDirection3Bundle(Direction3Bundle):
    source: Direction3Bundle
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> BundleDecision[Direction3Value]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledDirection3Bundle(Direction3Bundle):
    source: Direction3Bundle
    mapping: RosterMap

    def _decide(self) -> BundleDecision[Direction3Value]:
        return decide_relabeled(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _Direction3BundleAt(Direction3):
    bundle: Direction3Bundle
    key: Hashable

    def _decide(self) -> Direction3Decision:
        return decide_member_at(self.bundle, self.key)


@dataclass(frozen=True, eq=False)
class _Direction3BundleMean(Direction3):
    bundle: Direction3Bundle

    def _decide(self) -> Direction3Decision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("mean of an empty bundle is undefined")
                total = np.sum([direction.vector for direction in present], axis=0)
                if float(np.linalg.norm(total)) == 0.0:
                    return Unresolvable("the present directions cancel; their mean has no direction")
                return Resolvable(Direction3Value(vector=total))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
