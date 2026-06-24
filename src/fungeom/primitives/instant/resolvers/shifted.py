"""An instant advanced by a duration."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant


@dataclass(frozen=True, eq=False)
class ShiftedInstant(Instant):
    """``instant + by`` — resolvable iff both are. (Mirrors ``TranslatedPoint3``.)"""

    instant: Instant
    by: Duration

    def _decide(self) -> InstantDecision:
        match self.instant.decide(), self.by.decide():
            case Resolvable(base), Resolvable(shift):
                return Resolvable(base + shift)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
