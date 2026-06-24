"""Distance from a point to a 2D segment (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2DistanceTo(Scalar):
    """The distance from ``point`` to ``segment`` — total (non-negative)."""

    segment: Segment2
    point: Point2

    def _decide(self) -> ScalarDecision:
        match self.segment.decide(), self.point.decide():
            case Resolvable(segment), Resolvable(point):
                return Resolvable(segment.distance_to(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
