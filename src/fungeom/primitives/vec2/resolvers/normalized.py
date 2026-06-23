"""The unit vector in the direction of a 2D vector — partial at the origin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class NormalizedVec2(Vec2):
    """``vector / ‖vector‖`` — Unresolvable for the zero vector (no direction)."""

    vector: Vec2

    def _decide(self) -> Vec2Decision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        norm = float(np.linalg.norm(decided.value))
        if norm == 0.0:
            return Unresolvable("cannot normalize the zero vector")
        return Resolvable(decided.value / norm)
