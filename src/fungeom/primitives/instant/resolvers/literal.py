"""A resolver for an already-known instant, plus float coercion."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.instant.value import as_instant


@dataclass(frozen=True, eq=False)
class LiteralInstant(Instant):
    """An instant that is already known — always resolvable."""

    seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "seconds", as_instant(self.seconds))

    def _decide(self) -> InstantDecision:
        return Resolvable(self.seconds)


def as_instant_resolver(value: float | Instant) -> Instant:
    """Lift a bare number of master-clock seconds into a literal resolver.

    Pass instants through unchanged. This is the coercion that lets the fluent
    API accept plain floats while keeping every instant a graph node underneath.
    """
    if isinstance(value, Instant):
        return value
    return LiteralInstant(seconds=as_instant(value))
