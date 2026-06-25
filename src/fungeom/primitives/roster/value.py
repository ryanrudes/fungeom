"""The roster *value*: a finite set of entity keys — the support set of the nominal axis.

A :class:`RosterValue` is to the **entity** axis what a
:class:`~fungeom.primitives.coverage.value.CoverageValue` is to the **time** axis:
the honest answer to "over which part of the index is something defined". Where a
coverage is a set of disjoint *intervals*, a roster is a set of discrete *keys* — and
where the coverage algebra unions/intersects/subtracts spans, the roster algebra does
the same on keys. Storage is canonical: an **ordered, duplicate-free** tuple (first-seen
order), so the array layout of a :class:`~fungeom.Bundle` over a roster is reproducible;
but the *semantics* are order-free — two rosters with the same keys compare equal
regardless of order (equality and hashing key on the underlying *set*).

This module also exposes the set-algebra the roster resolvers are built from, as value
methods (:meth:`RosterValue.union` / :meth:`~RosterValue.intersection` /
:meth:`~RosterValue.difference`).
"""

from __future__ import annotations

from collections.abc import Hashable, Iterator
from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class RosterValue:
    """A canonical (ordered, duplicate-free) set of entity keys.

    ``keys`` is stored in first-seen order with duplicates removed. Equality is
    *set* equality (order-independent), so ``RosterValue(("a", "b")) ==
    RosterValue(("b", "a"))``; hashing matches.
    """

    keys: tuple[Hashable, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "keys", tuple(dict.fromkeys(self.keys)))

    def __contains__(self, key: Hashable) -> bool:
        return key in self.keys

    def __iter__(self) -> Iterator[Hashable]:
        return iter(self.keys)

    def __len__(self) -> int:
        return len(self.keys)

    @property
    def is_empty(self) -> bool:
        """Whether this roster contains no keys."""
        return not self.keys

    def union(self, other: RosterValue) -> RosterValue:
        """Every key in this roster *or* ``other`` (this roster's keys first)."""
        return RosterValue(keys=self.keys + other.keys)

    def intersection(self, other: RosterValue) -> RosterValue:
        """Every key in this roster *and* ``other`` (in this roster's order)."""
        return RosterValue(keys=tuple(key for key in self.keys if key in other))

    def difference(self, other: RosterValue) -> RosterValue:
        """Every key in this roster but *not* ``other`` (in this roster's order)."""
        return RosterValue(keys=tuple(key for key in self.keys if key not in other))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RosterValue) and frozenset(self.keys) == frozenset(other.keys)

    def __hash__(self) -> int:
        return hash(frozenset(self.keys))

    def __repr__(self) -> str:
        return f"RosterValue({{{', '.join(repr(key) for key in self.keys)}}})"
