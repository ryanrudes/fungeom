"""A resolver for an already-known direction."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value


@dataclass(frozen=True, eq=False)
class LiteralDirection3(Direction3):
    """A direction that is already known — always resolvable."""

    value: Direction3Value

    def _decide(self) -> Direction3Decision:
        return Resolvable(self.value)
