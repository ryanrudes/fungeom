"""A 2D vector assembled from two (deferred) scalar components."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2
from fungeom.primitives.vec2.value import as_vec2


@dataclass(frozen=True, eq=False)
class ComponentVec2(Vec2):
    """``(x, y)`` from two scalar resolvers."""

    x: Scalar
    y: Scalar

    def _decide(self) -> Vec2Decision:
        decided = gather([self.x.decide(), self.y.decide()])
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(as_vec2(np.array(decided.value, dtype=np.float64)))
