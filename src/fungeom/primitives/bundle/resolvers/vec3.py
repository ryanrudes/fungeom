"""``Vec3Bundle`` — a keyed collection of vectors."""

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
    decide_mapped,
    decide_member_at,
    decide_relabeled,
    decide_where,
    decide_zipped,
)
from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.value import Float3, as_vec3


class Vec3Bundle(Bundle[Float3]):
    """A deferred, keyed, possibly-masked collection of vectors.

    Construct with :meth:`of`, :meth:`from_array` (a raw ``(N, 3)`` array), or
    :meth:`from_map` (with an optional wider ``roster`` for absent keys); query with
    :meth:`at` (→ ``Vec3``), :meth:`present` / :meth:`count`, :meth:`where`, and fold
    with :meth:`mean` (→ ``Vec3``, the average over present members).
    """

    type Value = BundleValue[Float3]
    """The resolved value type — a keyed collection of vectors."""

    @classmethod
    def of(cls, vectors: Sequence[Vec3], keys: Sequence[Hashable] | None = None) -> Vec3Bundle:
        """A bundle from ``vectors``, keyed by ``keys`` (or by position ``0..N-1``)."""
        members = tuple(vectors)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredVec3Bundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_array(cls, vectors: ArrayLike, keys: Sequence[Hashable] | None = None) -> Vec3Bundle:
        """A bundle from a raw ``(N, 3)`` array; every vector is present."""
        rows = np.asarray(vectors, dtype=float).reshape(-1, 3)
        return cls.of(tuple(Vec3.of(float(x), float(y), float(z)) for x, y, z in rows), keys=keys)

    @classmethod
    def from_map(cls, vectors: Mapping[Hashable, Vec3], roster: Sequence[Hashable] | None = None) -> Vec3Bundle:
        """A bundle from a ``{key: vector}`` mapping, optionally over a larger ``roster``."""
        member_keys = tuple(vectors)
        members = tuple(vectors[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredVec3Bundle(member_keys=member_keys, members=members, roster=full)

    def at(self, key: Hashable) -> Vec3:
        """The vector for ``key`` (→ ``Vec3``); Unresolvable if absent or unknown."""
        return _Vec3BundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable] | Roster) -> Vec3Bundle:
        """The sub-bundle restricted to ``keys``."""
        return _WhereVec3Bundle(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def relabel(self, mapping: RosterMap) -> Vec3Bundle:
        """Rename keys through ``mapping`` (Unresolvable if it collapses keys onto one target)."""
        return _RelabeledVec3Bundle(source=self, mapping=mapping)

    def mean(self) -> Vec3:
        """The average of the present vectors (→ ``Vec3``); Unresolvable if none are."""
        return _Vec3BundleMean(bundle=self)

    def sum(self) -> Vec3:
        """The sum of the present vectors (→ ``Vec3``); the zero vector over an empty bundle."""
        return _Vec3BundleSum(bundle=self)

    def __add__(self, other: Vec3Bundle) -> Vec3Bundle:
        """Key-aligned sum with ``other`` (on the intersection of present keys)."""
        return _SumVec3Bundle(a=self, b=other)

    def __sub__(self, other: Vec3Bundle) -> Vec3Bundle:
        """Key-aligned difference with ``other``."""
        return _DiffVec3Bundle(a=self, b=other)

    def dot(self, other: Vec3Bundle) -> ScalarBundle:
        """Key-aligned dot product with ``other`` (→ ``ScalarBundle``)."""
        return _DotScalarBundle(a=self, b=other)

    def norm(self) -> ScalarBundle:
        """The key-by-key vector length (→ ``ScalarBundle``); a broadcast over the present members."""
        return _NormScalarBundle(source=self)


@dataclass(frozen=True, eq=False)
class _GatheredVec3Bundle(Vec3Bundle):
    member_keys: tuple[Hashable, ...]
    members: tuple[Vec3, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[Float3]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WhereVec3Bundle(Vec3Bundle):
    source: Vec3Bundle
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> BundleDecision[Float3]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledVec3Bundle(Vec3Bundle):
    source: Vec3Bundle
    mapping: RosterMap

    def _decide(self) -> BundleDecision[Float3]:
        return decide_relabeled(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _Vec3BundleAt(Vec3):
    bundle: Vec3Bundle
    key: Hashable

    def _decide(self) -> Vec3Decision:
        return decide_member_at(self.bundle, self.key)


@dataclass(frozen=True, eq=False)
class _Vec3BundleMean(Vec3):
    bundle: Vec3Bundle

    def _decide(self) -> Vec3Decision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("mean of an empty bundle is undefined")
                return Resolvable(as_vec3(np.mean(present, axis=0)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _Vec3BundleSum(Vec3):
    bundle: Vec3Bundle

    def _decide(self) -> Vec3Decision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                total = np.sum(present, axis=0) if present else np.zeros(3)
                return Resolvable(as_vec3(total))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _SumVec3Bundle(Vec3Bundle):
    a: Vec3Bundle
    b: Vec3Bundle

    def _decide(self) -> BundleDecision[Float3]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key) + self.b.at(key))


@dataclass(frozen=True, eq=False)
class _DiffVec3Bundle(Vec3Bundle):
    a: Vec3Bundle
    b: Vec3Bundle

    def _decide(self) -> BundleDecision[Float3]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key) - self.b.at(key))


@dataclass(frozen=True, eq=False)
class _DotScalarBundle(ScalarBundle):
    """The key-aligned dot product of two vector bundles — a cross-type lift to scalars."""

    a: Vec3Bundle
    b: Vec3Bundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key).dot(self.b.at(key)))


@dataclass(frozen=True, eq=False)
class _NormScalarBundle(ScalarBundle):
    """The key-by-key norm of a vector bundle — a cross-type broadcast to scalars."""

    source: Vec3Bundle

    def _decide(self) -> BundleDecision[float]:
        return decide_mapped(self.source, lambda key: self.source.at(key).norm())
