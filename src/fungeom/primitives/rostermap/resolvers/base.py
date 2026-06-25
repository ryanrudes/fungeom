"""The ``RosterMap`` interface — the identity correspondence between two rosters.

A roster map is the entity-axis analog of a :class:`~fungeom.TimeMap` (time) and a
:class:`~fungeom.Transform` (space): it relates one identity domain to another by a
partial key-to-key map ``source ↦ target``. You build one from an explicit mapping
(:meth:`of` — the landmark correspondences, the nominal-axis mirror of
``TimeMap.through``) or as the :meth:`identity` over a roster, and compose with ``@``
and :meth:`inverse` exactly as time maps do. **A roster map *is* motion retargeting at
the identity level** (which source marker is which target joint); the geometric transfer
on top is parked numerics. Sibling resolver types are imported lazily to keep module
load acyclic; the lower-layer ``Bool`` / ``Roster`` are imported normally.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.value import KeyCorrespondence


class RosterMap(Resolver[KeyCorrespondence]):
    """A deferred partial correspondence ``source key ↦ target key``.

    Construct one with :meth:`of` (an explicit ``{source: target}`` mapping — the
    correspondence landmarks), :meth:`identity` (each key of a roster to itself), or
    :meth:`known`; compose with ``@`` (:meth:`compose`) and :meth:`inverse`; read off the
    :meth:`source` / :meth:`target` rosters and probe membership with :meth:`maps`.
    ``resolve()`` yields a
    :class:`~fungeom.primitives.rostermap.value.KeyCorrespondence` (``RosterMap.Value``).

    The one *partial* operation is :meth:`inverse`: a non-injective correspondence (two
    sources sharing a target) has no inverse — the entity-axis analog of inverting a
    zero-rate time map. Composition is *total* (its domain just narrows to the keys that
    chain through).
    """

    type Value = KeyCorrespondence
    """The resolved value type — a :class:`KeyCorrespondence`."""

    @classmethod
    def known(cls, value: KeyCorrespondence) -> RosterMap:
        """Wrap an already-known :class:`KeyCorrespondence` value."""
        from fungeom.primitives.rostermap.resolvers.literal import LiteralRosterMap

        return LiteralRosterMap(pairs=dict(value.pairs))

    @classmethod
    def of(cls, mapping: Mapping[Hashable, Hashable]) -> RosterMap:
        """A correspondence from an explicit ``{source: target}`` mapping (the landmarks)."""
        from fungeom.primitives.rostermap.resolvers.literal import LiteralRosterMap

        return LiteralRosterMap(pairs=dict(mapping))

    @classmethod
    def identity(cls, keys: Roster | Sequence[Hashable]) -> RosterMap:
        """The identity correspondence over ``keys`` — each key mapped to itself.

        ``keys`` may be a concrete :class:`~fungeom.primitives.roster.resolvers.base.Roster`
        (e.g. a bundle's support) or a plain sequence of keys.
        """
        from fungeom.primitives.rostermap.resolvers.identity import IdentityRosterMap

        roster = keys if isinstance(keys, Roster) else Roster.of(tuple(keys))
        return IdentityRosterMap(roster=roster)

    def compose(self, inner: RosterMap) -> RosterMap:
        """``self ∘ inner`` — apply ``inner`` first, then this map (chain through shared keys)."""
        from fungeom.primitives.rostermap.resolvers.composed import ComposedRosterMap

        return ComposedRosterMap(outer=self, inner=inner)

    def __matmul__(self, other: RosterMap) -> RosterMap:
        return self.compose(other)

    def inverse(self) -> RosterMap:
        """The reversed correspondence (Unresolvable when not injective)."""
        from fungeom.primitives.rostermap.resolvers.inverse import InverseRosterMap

        return InverseRosterMap(rostermap=self)

    def source(self) -> Roster:
        """The source roster — every key this map corresponds *from* (→ ``Roster``)."""
        from fungeom.primitives.rostermap.resolvers.source import RosterMapSource

        return RosterMapSource(rostermap=self)

    def target(self) -> Roster:
        """The target roster — every key this map corresponds *to* (→ ``Roster``)."""
        from fungeom.primitives.rostermap.resolvers.target import RosterMapTarget

        return RosterMapTarget(rostermap=self)

    def maps(self, key: Hashable) -> Bool:
        """Whether ``key`` is in this map's source domain (→ ``Bool``)."""
        from fungeom.primitives.rostermap.resolvers.maps import RosterMapMaps

        return RosterMapMaps(rostermap=self, key=key)
