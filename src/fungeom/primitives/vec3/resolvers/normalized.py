"""The unit vector in the direction of a vector — partial at the origin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class NormalizedVec3(Vec3):
    """``vector / ‖vector‖`` — Unresolvable for the zero vector (no direction)."""

    vector: Vec3

    def _decide(self) -> Vec3Decision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        norm = float(np.linalg.norm(decided.value))
        if norm == 0.0:
            return Unresolvable("cannot normalize the zero vector")
        return Resolvable(decided.value / norm)
