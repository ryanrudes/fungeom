"""Distance from a point to a segment (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.segment.resolvers.base import Segment


@dataclass(frozen=True, eq=False)
class SegmentDistanceTo(Scalar):
    """The distance from ``point`` to ``segment`` — total (non-negative)."""

    segment: Segment
    point: Point3

    def _decide(self) -> ScalarDecision:
        match self.segment.decide(), self.point.decide():
            case Resolvable(segment), Resolvable(point):
                return Resolvable(segment.distance_to(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
