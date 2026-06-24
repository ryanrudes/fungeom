"""A segment's midpoint (→ Point3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.segment.resolvers.base import Segment


@dataclass(frozen=True, eq=False)
class SegmentMidpoint(Point3):
    """The point halfway along ``segment`` — total."""

    segment: Segment

    def _decide(self) -> Point3Decision:
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(Point3Value(coord=segment.midpoint(), frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
