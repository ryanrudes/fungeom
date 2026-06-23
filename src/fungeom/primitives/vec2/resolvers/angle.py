"""The unsigned angle between two 2D vectors, as a scalar — partial at the origin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class Vec2Angle(Scalar):
    """The angle (radians, in ``[0, π]``) between ``a`` and ``b``.

    Unresolvable if either vector is zero — the angle to a directionless vector
    is undefined.
    """

    a: Vec2
    b: Vec2

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
                if na == 0.0 or nb == 0.0:
                    return Unresolvable("angle with the zero vector is undefined")
                cosine = max(-1.0, min(1.0, float(np.dot(a, b)) / (na * nb)))
                return Resolvable(float(np.arccos(cosine)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
