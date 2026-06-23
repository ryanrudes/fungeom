"""The left perpendicular of a 2D vector (a 90° CCW turn)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class PerpendicularVec2(Vec2):
    """``(-y, x)`` — ``vector`` rotated 90° counter-clockwise; resolvable iff ``vector`` is."""

    vector: Vec2

    def _decide(self) -> Vec2Decision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        x, y = decided.value
        return Resolvable(np.array([-y, x], dtype=np.float64))
