"""The mean of several instants — the temporal analog of ``Point3.centroid``."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant


@dataclass(frozen=True, eq=False)
class CentroidInstant(Instant):
    """The average instant of the given collection.

    Instants form an affine space (durations are its difference space), so their
    average is well-defined. Resolvable only if every input is — and, as with the
    geometric centroid, never for an empty collection.
    """

    instants: tuple[Instant, ...]

    def _decide(self) -> InstantDecision:
        if not self.instants:
            return Unresolvable("centroid of no instants is undefined")
        decided = gather(i.decide() for i in self.instants)
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(sum(decided.value) / len(decided.value))
