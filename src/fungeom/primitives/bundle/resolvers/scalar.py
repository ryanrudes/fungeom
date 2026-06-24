"""``ScalarBundle`` — a keyed collection of scalars."""

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
    decide_where,
    decide_zipped,
)
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


class ScalarBundle(Bundle[float]):
    """A deferred, keyed, possibly-masked collection of scalars.

    Construct with :meth:`of`, :meth:`from_array` (a raw ``(N,)`` array), or
    :meth:`from_map` (with an optional wider ``roster`` for absent keys); query with
    :meth:`at` (→ ``Scalar``), :meth:`present` / :meth:`count`, :meth:`where`, and
    fold with :meth:`mean` (→ ``Scalar``, the average over present members).
    """

    type Value = BundleValue[float]
    """The resolved value type — a keyed collection of scalars."""

    @classmethod
    def of(cls, values: Sequence[Scalar], keys: Sequence[Hashable] | None = None) -> ScalarBundle:
        """A bundle from ``values``, keyed by ``keys`` (or by position ``0..N-1``)."""
        members = tuple(values)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredScalarBundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_array(cls, values: ArrayLike, keys: Sequence[Hashable] | None = None) -> ScalarBundle:
        """A bundle from a raw ``(N,)`` array; every value is present."""
        flat = np.asarray(values, dtype=float).reshape(-1)
        return cls.of(tuple(Scalar.of(float(v)) for v in flat), keys=keys)

    @classmethod
    def from_map(cls, values: Mapping[Hashable, Scalar], roster: Sequence[Hashable] | None = None) -> ScalarBundle:
        """A bundle from a ``{key: scalar}`` mapping, optionally over a larger ``roster``."""
        member_keys = tuple(values)
        members = tuple(values[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredScalarBundle(member_keys=member_keys, members=members, roster=full)

    def at(self, key: Hashable) -> Scalar:
        """The value for ``key`` (→ ``Scalar``); Unresolvable if absent or unknown."""
        return _ScalarBundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable]) -> ScalarBundle:
        """The sub-bundle restricted to ``keys``."""
        return _WhereScalarBundle(source=self, keep=tuple(keys))

    def mean(self) -> Scalar:
        """The average of the present values (→ ``Scalar``); Unresolvable if none are."""
        return _ScalarBundleMean(bundle=self)

    def sum(self) -> Scalar:
        """The sum of the present values (→ ``Scalar``); ``0`` over an empty bundle."""
        return _ScalarBundleSum(bundle=self)

    def min(self) -> Scalar:
        """The smallest present value (→ ``Scalar``); Unresolvable if none are."""
        return _ScalarBundleMin(bundle=self)

    def max(self) -> Scalar:
        """The largest present value (→ ``Scalar``); Unresolvable if none are."""
        return _ScalarBundleMax(bundle=self)

    def __add__(self, other: ScalarBundle) -> ScalarBundle:
        """Key-aligned sum with ``other`` (on the intersection of present keys)."""
        return _SumScalarBundle(a=self, b=other)

    def __sub__(self, other: ScalarBundle) -> ScalarBundle:
        """Key-aligned difference with ``other``."""
        return _DiffScalarBundle(a=self, b=other)

    def __mul__(self, other: ScalarBundle) -> ScalarBundle:
        """Key-aligned product with ``other``."""
        return _ProductScalarBundle(a=self, b=other)

    def __truediv__(self, other: ScalarBundle) -> ScalarBundle:
        """Key-aligned quotient with ``other`` (Unresolvable at a key where the divisor is zero)."""
        return _QuotientScalarBundle(a=self, b=other)


@dataclass(frozen=True, eq=False)
class _GatheredScalarBundle(ScalarBundle):
    member_keys: tuple[Hashable, ...]
    members: tuple[Scalar, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[float]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WhereScalarBundle(ScalarBundle):
    source: ScalarBundle
    keep: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[float]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _ScalarBundleAt(Scalar):
    bundle: ScalarBundle
    key: Hashable

    def _decide(self) -> ScalarDecision:
        return decide_member_at(self.bundle, self.key)


@dataclass(frozen=True, eq=False)
class _ScalarBundleMean(Scalar):
    bundle: ScalarBundle

    def _decide(self) -> ScalarDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("mean of an empty bundle is undefined")
                return Resolvable(float(np.mean(present)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _ScalarBundleSum(Scalar):
    bundle: ScalarBundle

    def _decide(self) -> ScalarDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(float(sum(collection.members[key] for key in collection.support())))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _ScalarBundleMin(Scalar):
    bundle: ScalarBundle

    def _decide(self) -> ScalarDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("min of an empty bundle is undefined")
                return Resolvable(float(np.min(present)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _ScalarBundleMax(Scalar):
    bundle: ScalarBundle

    def _decide(self) -> ScalarDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                present = [collection.members[key] for key in collection.support()]
                if not present:
                    return Unresolvable("max of an empty bundle is undefined")
                return Resolvable(float(np.max(present)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _SumScalarBundle(ScalarBundle):
    a: ScalarBundle
    b: ScalarBundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key) + self.b.at(key))


@dataclass(frozen=True, eq=False)
class _DiffScalarBundle(ScalarBundle):
    a: ScalarBundle
    b: ScalarBundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key) - self.b.at(key))


@dataclass(frozen=True, eq=False)
class _ProductScalarBundle(ScalarBundle):
    a: ScalarBundle
    b: ScalarBundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key) * self.b.at(key))


@dataclass(frozen=True, eq=False)
class _QuotientScalarBundle(ScalarBundle):
    a: ScalarBundle
    b: ScalarBundle

    def _decide(self) -> BundleDecision[float]:
        return decide_zipped(self.a, self.b, lambda key: self.a.at(key) / self.b.at(key))
