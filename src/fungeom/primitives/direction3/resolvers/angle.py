"""The angle between two directions, as a scalar."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Direction3Angle(Scalar):
    """The unsigned angle (radians) between ``a`` and ``b`` — resolvable iff both are."""

    a: Direction3
    b: Direction3

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a.angle_to(b))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
