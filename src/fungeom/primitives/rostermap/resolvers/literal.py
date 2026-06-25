"""A roster map built from an explicit key mapping."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.rostermap.decidability import RosterMapDecision
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.rostermap.value import KeyCorrespondence


@dataclass(frozen=True, eq=False)
class LiteralRosterMap(RosterMap):
    """The correspondence given by ``pairs`` (``{source: target}``).

    Always resolvable — the pairs are plain values; the empty mapping is the
    (resolvable) empty correspondence.
    """

    pairs: dict[Hashable, Hashable]

    def _decide(self) -> RosterMapDecision:
        return Resolvable(KeyCorrespondence(pairs=self.pairs))
