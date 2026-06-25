"""The ``Roster`` interface and its key-set algebra.

A roster is the identity domain for the **entity** axis — the nominal-axis analog of
:class:`~fungeom.primitives.timeline.resolvers.base.Timeline` (time) and
:class:`~fungeom.Frame` (space), and the discrete counterpart of a
:class:`~fungeom.Coverage` (a set of keys vs a set of intervals). Its algebra mirrors
the coverage algebra exactly, one axis over: :meth:`union` / :meth:`intersection` /
:meth:`difference` are *total* (the result may just be empty), and the support of a
:class:`~fungeom.Bundle` is a roster. Sibling resolver types are imported lazily to keep
module load acyclic; the lower-layer ``Bool`` / ``Scalar`` are imported normally.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from typing import ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.roster.value import RosterValue
from fungeom.primitives.scalar.resolvers.base import Scalar


class Roster(Resolver[RosterValue]):
    """A deferred set of entity keys — the support set of the nominal axis.

    Construct one with :meth:`of` (from a collection of keys, deduplicated) or the
    :attr:`empty` constant; compose with :meth:`union` / :meth:`intersection` /
    :meth:`difference` (→ ``Roster``), :meth:`count` (→ ``Scalar``), and the predicate
    :meth:`contains` (→ :class:`~fungeom.Bool`). ``resolve()`` yields a
    :class:`~fungeom.primitives.roster.value.RosterValue` (``Roster.Value``).

    The set algebra is *total* — keys carry no partiality of their own, so a roster is
    ``Unresolvable`` only by *propagation* (e.g. the support of an unresolvable bundle).
    """

    type Value = RosterValue
    """The resolved value type — a :class:`RosterValue`."""

    empty: ClassVar[Roster]
    """The empty roster, as a resolver. (Assigned once ``LiteralRoster`` exists.)"""

    @classmethod
    def of(cls, keys: Sequence[Hashable]) -> Roster:
        """A roster of ``keys`` (deduplicated, first-seen order kept)."""
        from fungeom.primitives.roster.resolvers.literal import LiteralRoster

        return LiteralRoster(keys=tuple(keys))

    def union(self, other: Roster) -> Roster:
        """Every key in this roster *or* ``other``."""
        from fungeom.primitives.roster.resolvers.union import RosterUnion

        return RosterUnion(a=self, b=other)

    def intersection(self, other: Roster) -> Roster:
        """Every key in this roster *and* ``other``."""
        from fungeom.primitives.roster.resolvers.intersection import RosterIntersection

        return RosterIntersection(a=self, b=other)

    def difference(self, other: Roster) -> Roster:
        """Every key in this roster but *not* ``other`` (empty when ``other`` swallows it)."""
        from fungeom.primitives.roster.resolvers.difference import RosterDifference

        return RosterDifference(a=self, b=other)

    def count(self) -> Scalar:
        """How many keys are in the roster — its cardinality (→ ``Scalar``)."""
        from fungeom.primitives.roster.resolvers.count import RosterCount

        return RosterCount(roster=self)

    def contains(self, key: Hashable) -> Bool:
        """Whether ``key`` is a member of this roster (→ ``Bool``)."""
        from fungeom.primitives.roster.resolvers.contains import RosterContains

        return RosterContains(roster=self, key=key)
