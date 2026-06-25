"""The roster-map *value*: a partial correspondence between two sets of entity keys.

A :class:`KeyCorrespondence` is to the **entity** axis what an
:class:`~fungeom.primitives.timemap.value.AffineTimeMap` is to **time** and a
:class:`~fungeom.RigidTransform` is to **space** — the map between two identity domains.
It carries only the **identity** correspondence (*which* source entity is which target
entity: source-skeleton markers ↦ target-skeleton joints), a partial function from
source keys to target keys. **This is what motion retargeting is** at the identity level;
the *geometric* transfer (where a target joint actually goes) is a fitted map layered on
top, not part of this value — exactly as ``TimeMap.through`` recovers the alignment while
the estimator that discovers the landmarks stays parked.

Composition mirrors ``AffineTimeMap`` (and SE(3)) one axis over; inversion is partial,
defined only for an **injective** correspondence (no two sources share a target) — the
nominal-axis analog of a zero-rate (non-invertible) time map.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class KeyCorrespondence:
    """A partial map ``source key ↦ target key`` (stored as an ordered ``pairs`` dict)."""

    pairs: dict[Hashable, Hashable]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pairs", dict(self.pairs))

    def maps(self, key: Hashable) -> bool:
        """Whether ``key`` is in the source domain of this correspondence."""
        return key in self.pairs

    def apply(self, key: Hashable) -> Hashable:
        """The target for a source ``key`` (caller checks :meth:`maps` first)."""
        return self.pairs[key]

    @property
    def source_keys(self) -> tuple[Hashable, ...]:
        """The source domain — every key this correspondence maps *from*."""
        return tuple(self.pairs)

    @property
    def target_keys(self) -> tuple[Hashable, ...]:
        """The target image — every key this correspondence maps *to* (deduplicated)."""
        return tuple(dict.fromkeys(self.pairs.values()))

    @property
    def is_injective(self) -> bool:
        """Whether distinct sources map to distinct targets (so the map is invertible)."""
        return len(set(self.pairs.values())) == len(self.pairs)

    def inverse(self) -> KeyCorrespondence:
        """The reversed correspondence ``target ↦ source`` (defined only when injective)."""
        return KeyCorrespondence(pairs={target: source for source, target in self.pairs.items()})

    def compose(self, inner: KeyCorrespondence) -> KeyCorrespondence:
        """``self ∘ inner`` — apply ``inner`` first, then ``self`` (chaining through shared keys)."""
        return KeyCorrespondence(pairs={key: self.pairs[mid] for key, mid in inner.pairs.items() if mid in self.pairs})

    def __eq__(self, other: object) -> bool:
        return isinstance(other, KeyCorrespondence) and self.pairs == other.pairs

    def __hash__(self) -> int:
        return hash(frozenset(self.pairs.items()))

    def __repr__(self) -> str:
        return f"KeyCorrespondence({len(self.pairs)} pairs)"
