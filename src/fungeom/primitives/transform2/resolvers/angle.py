"""A 2D transform's rotation angle (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class Transform2Angle(Scalar):
    """``transform``'s rotation angle (radians), in ``(-π, π]`` — total."""

    transform: Transform2

    def _decide(self) -> ScalarDecision:
        match self.transform.decide():
            case Resolvable(transform):
                return Resolvable(transform.angle())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
