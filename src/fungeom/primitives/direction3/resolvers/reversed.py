"""The opposite of a direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3


@dataclass(frozen=True, eq=False)
class ReversedDirection3(Direction3):
    """``-direction`` — resolvable iff ``direction`` is."""

    direction: Direction3

    def _decide(self) -> Direction3Decision:
        decided = self.direction.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(decided.value.reversed())
