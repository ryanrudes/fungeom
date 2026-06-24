"""The bundle *value*: a finite, keyed, partial collection of ``V`` values.

A :class:`BundleValue` is the resolved form of a :class:`~fungeom.Bundle` — a field
over a *nominal* axis (entities), the discrete counterpart of a signal's
:class:`~fungeom.primitives.signals.series.SampledSeries` over the continuous time
axis. It carries a **roster** (every declared key, in canonical order) and the
**members** present for those keys; the *support* is the present subset. A masked
collection (an occluded marker) is one whose support is a strict subset of its
roster — support is first-class and total, exactly as a signal's ``Coverage`` is, so
there is no separate "complete" vs "partial" type.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class BundleValue[V]:
    """A keyed collection: a ``roster`` of declared keys and the present ``members``.

    Generic over the member value type ``V``. ``members`` is always a subset of
    ``roster`` (the resolver guarantees it); the keys present in ``members`` are the
    collection's *support*. Equality is identity-based (``eq=False``).
    """

    roster: tuple[Hashable, ...]
    members: dict[Hashable, V]

    def __post_init__(self) -> None:
        object.__setattr__(self, "roster", tuple(self.roster))
        object.__setattr__(self, "members", dict(self.members))

    def support(self) -> tuple[Hashable, ...]:
        """The present keys, in roster (canonical) order — where the collection is defined."""
        return tuple(key for key in self.roster if key in self.members)

    def present(self, key: Hashable) -> bool:
        """Whether ``key`` has a value in this collection."""
        return key in self.members

    def at(self, key: Hashable) -> V:
        """The value for a present ``key`` (caller checks :meth:`present` first)."""
        return self.members[key]

    @property
    def count(self) -> int:
        """How many keys are present (the size of the support)."""
        return len(self.members)

    def __repr__(self) -> str:
        absent = len(self.roster) - len(self.members)
        suffix = f", {absent} absent" if absent else ""
        return f"BundleValue({self.count} of {len(self.roster)} keys{suffix})"
