"""The direction of a (deferred) 2D vector — partial at the origin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class NormalizedDirection2(Direction2):
    """The direction of ``vector`` — Unresolvable for the zero vector."""

    vector: Vec2

    def _decide(self) -> Direction2Decision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        if float(np.linalg.norm(decided.value)) == 0.0:
            return Unresolvable("cannot take the direction of the zero vector")
        return Resolvable(Direction2Value(vector=decided.value))
