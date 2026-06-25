"""``TransformBundle`` — a keyed collection of rigid transforms.

Unlike the other facades there is no ``from_array`` (a rigid transform has no
ergonomic raw form — like ``TransformSignal``, it is built from ``Transform``
values) and no fold: an SE(3) average is a numerics kernel, which fungeom *calls*
rather than *is*. So this facade is construction + ``at`` + ``where`` only.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass

from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.base import (
    Bundle,
    decide_gathered,
    decide_member_at,
    decide_relabeled,
    decide_where,
)
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform


class TransformBundle(Bundle[RigidTransform]):
    """A deferred, keyed, possibly-masked collection of rigid transforms.

    Construct with :meth:`of` or :meth:`from_map` (with an optional wider ``roster``
    for absent keys); query with :meth:`at` (→ ``Transform``), :meth:`present` /
    :meth:`count`, and :meth:`where`. There is no fold — averaging on SE(3) is
    numerics, deliberately out of scope.
    """

    type Value = BundleValue[RigidTransform]
    """The resolved value type — a keyed collection of rigid transforms."""

    @classmethod
    def of(cls, transforms: Sequence[Transform], keys: Sequence[Hashable] | None = None) -> TransformBundle:
        """A bundle from ``transforms``, keyed by ``keys`` (or by position ``0..N-1``)."""
        members = tuple(transforms)
        member_keys = tuple(keys) if keys is not None else tuple(range(len(members)))
        return _GatheredTransformBundle(member_keys=member_keys, members=members, roster=member_keys)

    @classmethod
    def from_map(
        cls,
        transforms: Mapping[Hashable, Transform],
        roster: Sequence[Hashable] | None = None,
    ) -> TransformBundle:
        """A bundle from a ``{key: transform}`` mapping, optionally over a larger ``roster``."""
        member_keys = tuple(transforms)
        members = tuple(transforms[key] for key in member_keys)
        full = tuple(dict.fromkeys([*roster, *member_keys])) if roster is not None else member_keys
        return _GatheredTransformBundle(member_keys=member_keys, members=members, roster=full)

    def at(self, key: Hashable) -> Transform:
        """The transform for ``key`` (→ ``Transform``); Unresolvable if absent or unknown."""
        return _TransformBundleAt(bundle=self, key=key)

    def where(self, keys: Sequence[Hashable]) -> TransformBundle:
        """The sub-bundle restricted to ``keys``."""
        return _WhereTransformBundle(source=self, keep=tuple(keys))

    def relabel(self, mapping: RosterMap) -> TransformBundle:
        """Rename keys through ``mapping`` (Unresolvable if it collapses keys onto one target)."""
        return _RelabeledTransformBundle(source=self, mapping=mapping)


@dataclass(frozen=True, eq=False)
class _GatheredTransformBundle(TransformBundle):
    member_keys: tuple[Hashable, ...]
    members: tuple[Transform, ...]
    roster: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[RigidTransform]:
        return decide_gathered(self.member_keys, self.members, self.roster)


@dataclass(frozen=True, eq=False)
class _WhereTransformBundle(TransformBundle):
    source: TransformBundle
    keep: tuple[Hashable, ...]

    def _decide(self) -> BundleDecision[RigidTransform]:
        return decide_where(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledTransformBundle(TransformBundle):
    source: TransformBundle
    mapping: RosterMap

    def _decide(self) -> BundleDecision[RigidTransform]:
        return decide_relabeled(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _TransformBundleAt(Transform):
    bundle: TransformBundle
    key: Hashable

    def _decide(self) -> RigidTransformDecision:
        return decide_member_at(self.bundle, self.key)
