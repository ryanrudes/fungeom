"""A roster built from a collection of keys."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.roster.decidability import RosterDecision
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.roster.value import RosterValue


@dataclass(frozen=True, eq=False)
class LiteralRoster(Roster):
    """The roster of ``keys`` (deduplicated on resolution).

    Always resolvable — keys are plain values, so the empty collection is the
    (resolvable) empty roster.
    """

    keys: tuple[Hashable, ...]

    def _decide(self) -> RosterDecision:
        return Resolvable(RosterValue(keys=self.keys))
