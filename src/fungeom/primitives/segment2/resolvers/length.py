"""A 2D segment's length (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.segment2.resolvers.base import Segment2


@dataclass(frozen=True, eq=False)
class Segment2Length(Scalar):
    """``segment``'s length — total (non-negative)."""

    segment: Segment2

    def _decide(self) -> ScalarDecision:
        match self.segment.decide():
            case Resolvable(segment):
                return Resolvable(segment.length())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
