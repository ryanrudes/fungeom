"""The time-map *value*: an affine reparametrization of time.

An :class:`AffineTimeMap` is the 1-D analog of a :class:`RigidTransform` — the map
``parent = offset + rate · local`` that relates one clock's seconds to another's.
It is the glue between timelines: a clock knows the affine map from its own
seconds into its parent's, and chaining those maps is how a local instant becomes
master-anchored. Composition and inversion mirror SE(3) exactly, one dimension
down; a map with zero ``rate`` (a frozen clock) is not invertible.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AffineTimeMap:
    """An affine clock map ``t ↦ offset + rate · t`` (offset in seconds)."""

    offset: float
    rate: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "offset", float(self.offset))
        object.__setattr__(self, "rate", float(self.rate))

    @classmethod
    def identity(cls) -> AffineTimeMap:
        """The identity map (no shift, unit rate)."""
        return cls(offset=0.0, rate=1.0)

    def apply(self, t: float) -> float:
        """Map a local time ``t`` through this map."""
        return self.offset + self.rate * t

    def compose(self, inner: AffineTimeMap) -> AffineTimeMap:
        """``self ∘ inner`` — apply ``inner`` first, then ``self``."""
        return AffineTimeMap(
            offset=self.offset + self.rate * inner.offset,
            rate=self.rate * inner.rate,
        )

    @property
    def is_invertible(self) -> bool:
        """Whether this map can be inverted (its rate is non-zero)."""
        return self.rate != 0.0

    def inverse(self) -> AffineTimeMap:
        """The inverse map (parent → local). Defined only when :attr:`is_invertible`."""
        return AffineTimeMap(offset=-self.offset / self.rate, rate=1.0 / self.rate)

    def approx_equal(self, other: AffineTimeMap, atol: float = 1e-9) -> bool:
        """Numeric comparison of two maps within ``atol``."""
        return abs(self.offset - other.offset) <= atol and abs(self.rate - other.rate) <= atol

    def __repr__(self) -> str:
        return f"AffineTimeMap(offset={self.offset:g}, rate={self.rate:g})"
