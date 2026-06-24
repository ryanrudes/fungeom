"""Spherical interpolation between two 2D directions — partial when they are antipodal."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class SlerpDirection2(Direction2):
    """Rotate ``a`` toward ``b`` by a fraction ``t`` of the angle between them.

    Unresolvable when ``a`` and ``b`` are antipodal (their shortest geodesic on the circle
    is ambiguous — a half turn could go either way). ``t`` itself may be deferred.
    """

    a: Direction2
    b: Direction2
    t: Scalar

    def _decide(self) -> Direction2Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(a), Resolvable(b), Resolvable(t):
                perp = float(a.vector[0] * b.vector[1] - a.vector[1] * b.vector[0])
                dot = float(np.dot(a.vector, b.vector))
                if perp == 0.0 and dot < 0.0:
                    return Unresolvable("antipodal directions have no unique interpolation")
                phi = t * float(np.arctan2(perp, dot))
                cos, sin = np.cos(phi), np.sin(phi)
                rotated = [a.vector[0] * cos - a.vector[1] * sin, a.vector[0] * sin + a.vector[1] * cos]
                return Resolvable(Direction2Value(vector=np.array(rotated)))
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
