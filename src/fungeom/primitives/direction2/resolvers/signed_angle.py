"""The signed (counter-clockwise) angle between two 2D directions (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Direction2SignedAngle(Scalar):
    """The signed angle (radians) from ``a`` to ``b``, in ``(-π, π]`` — positive counter-clockwise.

    Total: ``atan2(aₓbᵧ − aᵧbₓ, a · b)``. Unlike the unsigned :meth:`Direction2.angle_to`,
    this carries the plane's orientation — a 2D-only notion (3D directions have no sign).
    """

    a: Direction2
    b: Direction2

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                perp = float(a.vector[0] * b.vector[1] - a.vector[1] * b.vector[0])
                dot = float(np.dot(a.vector, b.vector))
                return Resolvable(float(np.arctan2(perp, dot)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
