"""Perpendicular distance from a point to a line (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class LineDistanceTo(Scalar):
    """The perpendicular distance from ``point`` to ``line`` — total (non-negative)."""

    line: Line
    point: Point3

    def _decide(self) -> ScalarDecision:
        match self.line.decide(), self.point.decide():
            case Resolvable(line), Resolvable(point):
                return Resolvable(line.distance_to(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
