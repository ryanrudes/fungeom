"""A 2D line's unit direction (→ Direction2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.line2.resolvers.base import Line2


@dataclass(frozen=True, eq=False)
class Line2Direction(Direction2):
    """``line``'s unit direction — total."""

    line: Line2

    def _decide(self) -> Direction2Decision:
        match self.line.decide():
            case Resolvable(line):
                return Resolvable(Direction2Value(vector=line.direction))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
