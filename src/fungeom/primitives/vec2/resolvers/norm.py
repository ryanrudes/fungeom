"""The Euclidean length of a 2D vector, as a scalar."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class Vec2Norm(Scalar):
    """``‖vector‖`` — resolvable iff the vector is."""

    vector: Vec2

    def _decide(self) -> ScalarDecision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(float(np.linalg.norm(decided.value)))
