"""The inverse of a roster map — partial when the correspondence is not injective."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.rostermap.decidability import RosterMapDecision
from fungeom.primitives.rostermap.resolvers.base import RosterMap


@dataclass(frozen=True, eq=False)
class InverseRosterMap(RosterMap):
    """The reversed correspondence ``target ↦ source``.

    Unresolvable when ``rostermap`` is not injective — two sources sharing a target give
    the inverse no single answer, the entity-axis analog of inverting a zero-rate clock.
    """

    rostermap: RosterMap

    def _decide(self) -> RosterMapDecision:
        match self.rostermap.decide():
            case Resolvable(value):
                if not value.is_injective:
                    return Unresolvable("a non-injective roster map (two sources share a target) is not invertible")
                return Resolvable(value.inverse())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
