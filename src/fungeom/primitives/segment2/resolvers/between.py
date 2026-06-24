"""A 2D segment from two endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.segment2.decidability import Segment2Decision
from fungeom.primitives.segment2.resolvers.base import Segment2
from fungeom.primitives.segment2.value import Segment2Value


@dataclass(frozen=True, eq=False)
class Segment2Between(Segment2):
    """The segment from ``a`` to ``b``."""

    a: Point2
    b: Point2

    def _decide(self) -> Segment2Decision:
        match self.a.decide(), self.b.decide():
            case Resolvable(start), Resolvable(end):
                return Resolvable(Segment2Value(start=start.coord, end=end.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
