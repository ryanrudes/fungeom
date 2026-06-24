"""Signed distance from a point to a 2D line (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Line2SignedDistance(Scalar):
    """The signed distance from ``point`` to ``line`` — total (positive on the left-normal side)."""

    line: Line2
    point: Point2

    def _decide(self) -> ScalarDecision:
        match self.line.decide(), self.point.decide():
            case Resolvable(line), Resolvable(point):
                return Resolvable(line.signed_distance(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
