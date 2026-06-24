"""A resolver for an already-known 2D direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value


@dataclass(frozen=True, eq=False)
class LiteralDirection2(Direction2):
    """A direction that is already known — always resolvable."""

    value: Direction2Value

    def _decide(self) -> Direction2Decision:
        return Resolvable(self.value)
