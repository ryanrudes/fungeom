"""``BoolBundle`` — a keyed collection of truth values (the output of per-key predicates).

The collection produced by broadcasting a predicate over a cloud — ``Plane.contains(cloud)``,
``Region2.contains(cloud)``, a per-marker comparison. Carries the key-aligned logical algebra
(``and_`` / ``or_`` / ``not_``) and the folds ``any`` / ``all`` (→ ``Bool``), the contact-spine
reductions ("is *any* corner in contact?", "are *all* markers inside?").
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
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
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.resolvers.base import RosterMap


class BoolBundle(Bundle[bool]):
    """A deferred, keyed, possibly-masked collection of truth values.

    Construct with :meth:`of`, :meth:`from_array` (a raw ``(N,)`` bool array), or
    :meth:`from_map`; query with :meth:`at` (→ ``Bool``), :meth:`present` / :meth:`count` /
    :meth:`where`; combine key-by-key with :meth:`and_` / :meth:`or_` / :meth:`not_`
    (``&`` / ``|`` / ``~``); and fold with :meth:`any` / :meth:`all` (→ ``Bool``).
    """

    type Value = BundleValue[bool]
    """The resolved value type — a keyed collection of booleans."""

    @classmethod
    def of(cls, values: Sequence[Bool], keys: Sequence[Hashable] | None = None) -> BoolBundle:
        """A bundle from ``values``, keyed by ``keys`` (or by position ``0..N-1``)."""
        members = tuple(values)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredBoolBundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_array(cls, values: ArrayLike, keys: Sequence[Hashable] | None = None) -> BoolBundle:
        """A bundle from a raw ``(N,)`` boolean array; every value is present."""
        flat = np.asarray(values, dtype=bool).reshape(-1)
        return cls.of(tuple(Bool.of(bool(v)) for v in flat), keys=keys)

    @classmethod
    def from_map(cls, values: Mapping[Hashable, Bool], roster: Sequence[Hashable] | None = None) -> BoolBundle:
        """A bundle from a ``{key: bool}`` mapping, optionally over a larger ``roster``."""
        member_keys = tuple(values)
        members = tuple(values[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredBoolBundle(member_keys=member_keys, members=members, roster=full)

    def at(self, key: Hashable) -> Bool:
        """The truth value for ``key`` (→ ``Bool``); Unresolvable if absent or unknown."""
        return _BoolBundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable] | Roster) -> BoolBundle:
        """The sub-bundle restricted to ``keys``."""
        return _WhereBoolBundle(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def relabel(self, mapping: RosterMap) -> BoolBundle:
        """Rename keys through ``mapping`` (Unresolvable if it collapses keys onto one target)."""
        return _RelabeledBoolBundle(source=self, mapping=mapping)

    def and_(self, other: BoolBundle) -> BoolBundle:
        """Key-aligned conjunction with ``other`` (on the intersection of present keys)."""
        return _AndBoolBundle(a=self, b=other)

    def or_(self, other: BoolBundle) -> BoolBundle:
        """Key-aligned disjunction with ``other``."""
        return _OrBoolBundle(a=self, b=other)

    def not_(self) -> BoolBundle:
        """The per-key negation (preserves the roster)."""
        return _NotBoolBundle(source=self)

    def __and__(self, other: BoolBundle) -> BoolBundle:
        return self.and_(other)

    def __or__(self, other: BoolBundle) -> BoolBundle:
        return self.or_(other)

    def __invert__(self) -> BoolBundle:
        return self.not_()

    def any(self) -> Bool:
        """Whether *any* present member is true (→ ``Bool``; ``False`` over an empty bundle)."""
        return _BoolBundleAny(bundle=self)

    def all(self) -> Bool:
        """Whether *every* present member is true (→ ``Bool``; ``True`` over an empty bundle)."""
        return _BoolBundleAll(bundle=self)


@dataclass(frozen=True, eq=False)
class _GatheredBoolBundle(BoolBundle):
    member_keys: tuple[Hashable, ...]
    members: tuple[Bool, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[bool]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WhereBoolBundle(BoolBundle):
    source: BoolBundle
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> BundleDecision[bool]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledBoolBundle(BoolBundle):
    source: BoolBundle
    mapping: RosterMap

    def _decide(self) -> BundleDecision[bool]:
        return decide_relabeled(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _BoolBundleAt(Bool):
    bundle: BoolBundle
    key: Hashable

    def _decide(self) -> BoolDecision:
        return decide_member_at(self.bundle, self.key)


@dataclass(frozen=True, eq=False)
class _AndBoolBundle(BoolBundle):
    a: BoolBundle
    b: BoolBundle

    def _decide(self) -> BundleDecision[bool]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key).and_(self.b.at(key)))


@dataclass(frozen=True, eq=False)
class _OrBoolBundle(BoolBundle):
    a: BoolBundle
    b: BoolBundle

    def _decide(self) -> BundleDecision[bool]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key).or_(self.b.at(key)))


@dataclass(frozen=True, eq=False)
class _NotBoolBundle(BoolBundle):
    source: BoolBundle

    def _decide(self) -> BundleDecision[bool]:
        return decide_mapped(self.source, lambda key: self.source.at(key).not_())


@dataclass(frozen=True, eq=False)
class _BoolBundleAny(Bool):
    bundle: BoolBundle

    def _decide(self) -> BoolDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(any(collection.members[key] for key in collection.support()))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BoolBundleAll(Bool):
    bundle: BoolBundle

    def _decide(self) -> BoolDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(all(collection.members[key] for key in collection.support()))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BundlePresenceMask(BoolBundle):
    """The occlusion mask of any ``source`` bundle — each declared key → whether it is present."""

    source: Bundle[Any]

    def _decide(self) -> BundleDecision[bool]:
        match self.source.decide():
            case Resolvable(collection):
                members: dict[Hashable, bool] = {key: collection.present(key) for key in collection.roster}
                return Resolvable(BundleValue(roster=collection.roster, members=members))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
