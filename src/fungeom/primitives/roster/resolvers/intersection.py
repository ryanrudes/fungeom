"""The intersection of two rosters."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.roster.decidability import RosterDecision
from fungeom.primitives.roster.resolvers.base import Roster


@dataclass(frozen=True, eq=False)
class RosterIntersection(Roster):
    """Every key in ``a`` and ``b`` (total — empty when they share none)."""

    a: Roster
    b: Roster

    def _decide(self) -> RosterDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a.intersection(b))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
