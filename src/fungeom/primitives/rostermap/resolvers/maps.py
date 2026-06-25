"""Membership of a key in a roster map's source domain — resolving to a ``Bool``."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.rostermap.resolvers.base import RosterMap


@dataclass(frozen=True, eq=False)
class RosterMapMaps(Bool):
    """Whether ``key`` is in the source domain of ``rostermap``."""

    rostermap: RosterMap
    key: Hashable

    def _decide(self) -> BoolDecision:
        match self.rostermap.decide():
            case Resolvable(value):
                return Resolvable(value.maps(self.key))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
