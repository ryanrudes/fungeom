"""A line's unit direction (→ Direction3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.line.resolvers.base import Line


@dataclass(frozen=True, eq=False)
class LineDirection(Direction3):
    """``line``'s unit direction — total (a line always has one)."""

    line: Line

    def _decide(self) -> Direction3Decision:
        match self.line.decide():
            case Resolvable(line):
                return Resolvable(Direction3Value(vector=line.direction))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
