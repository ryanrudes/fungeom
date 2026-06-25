"""The identity correspondence over a roster — each key mapped to itself."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.decidability import RosterMapDecision
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.rostermap.value import KeyCorrespondence


@dataclass(frozen=True, eq=False)
class IdentityRosterMap(RosterMap):
    """Each key of ``roster`` mapped to itself — Unresolvable iff ``roster`` is."""

    roster: Roster

    def _decide(self) -> RosterMapDecision:
        match self.roster.decide():
            case Resolvable(value):
                return Resolvable(KeyCorrespondence(pairs={key: key for key in value.keys}))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
