"""A 2D point linearly interpolated between two others."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Lerp2(Point2):
    """``(1 - t) * a + t * b`` — resolvable iff both endpoints and ``t`` are."""

    a: Point2
    b: Point2
    t: Scalar

    def _decide(self) -> Point2Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(va), Resolvable(vb), Resolvable(t):
                coord = va.coord * (1.0 - t) + vb.coord * t
                return Resolvable(Point2Value(coord=coord, frame=WORLD_FRAME2))
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
