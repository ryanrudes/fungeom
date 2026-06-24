"""The clamped parameter of a point along a 2D segment (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2ParameterOf(Scalar):
    """The clamped parameter in ``[0, 1]`` of ``point``'s closest point on ``segment`` — total."""

    segment: Segment2
    point: Point2

    def _decide(self) -> ScalarDecision:
        match self.segment.decide(), self.point.decide():
            case Resolvable(segment), Resolvable(point):
                return Resolvable(segment.parameter(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
