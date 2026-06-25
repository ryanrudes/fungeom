"""The target roster of a roster map — resolving to a ``Roster``."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.roster.decidability import RosterDecision
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.roster.value import RosterValue
from fungeom.primitives.rostermap.resolvers.base import RosterMap


@dataclass(frozen=True, eq=False)
class RosterMapTarget(Roster):
    """The target image of ``rostermap`` — every key it corresponds *to* (deduplicated)."""

    rostermap: RosterMap

    def _decide(self) -> RosterDecision:
        match self.rostermap.decide():
            case Resolvable(value):
                return Resolvable(RosterValue(keys=value.target_keys))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
