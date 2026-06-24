"""A line's representative point (→ Point3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class LineOrigin(Point3):
    """``line``'s representative point — total."""

    line: Line

    def _decide(self) -> Point3Decision:
        match self.line.decide():
            case Resolvable(line):
                return Resolvable(Point3Value(coord=line.point, frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
