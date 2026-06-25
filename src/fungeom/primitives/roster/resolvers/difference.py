"""The difference of two rosters."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.roster.decidability import RosterDecision
from fungeom.primitives.roster.resolvers.base import Roster


@dataclass(frozen=True, eq=False)
class RosterDifference(Roster):
    """Every key in ``a`` but not ``b`` (total — empty when ``b`` swallows ``a``)."""

    a: Roster
    b: Roster

    def _decide(self) -> RosterDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a.difference(b))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
