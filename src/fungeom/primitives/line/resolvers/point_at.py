"""A point at a signed arc-length along a line (→ Point3) — total (a line is infinite)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class LinePointAt(Point3):
    """The point at signed arc-length ``distance`` along ``line`` from its origin — total."""

    line: Line
    distance: float

    def _decide(self) -> Point3Decision:
        match self.line.decide():
            case Resolvable(line):
                return Resolvable(Point3Value(coord=line.point_at(self.distance), frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
