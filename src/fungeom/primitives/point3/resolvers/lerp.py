"""A point linearly interpolated between two others."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Lerp3(Point3):
    """``(1 - t) * a + t * b`` — resolvable iff both endpoints and ``t`` are."""

    a: Point3
    b: Point3
    t: Scalar

    def _decide(self) -> Point3Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(va), Resolvable(vb), Resolvable(t):
                coord = va.coord * (1.0 - t) + vb.coord * t
                return Resolvable(Point3Value(coord=coord, frame=WORLD_FRAME))
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
