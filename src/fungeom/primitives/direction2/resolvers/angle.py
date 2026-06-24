"""A 2D direction's oriented angle from +x (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Direction2OrientedAngle(Scalar):
    """``direction``'s angle (radians) from +x, in ``(-π, π]`` — total."""

    direction: Direction2

    def _decide(self) -> ScalarDecision:
        match self.direction.decide():
            case Resolvable(value):
                return Resolvable(value.angle())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
