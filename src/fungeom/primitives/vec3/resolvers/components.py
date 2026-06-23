"""A vector assembled from three (deferred) scalar components.

The fully consistent counterpart to ``LiteralVec3``: where the literal takes
concrete floats, this takes three ``Scalar`` components — so a vector can
be built from, say, another vector's norm. Resolvable iff all three are.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.value import as_vec3


@dataclass(frozen=True, eq=False)
class ComponentVec3(Vec3):
    """``(x, y, z)`` from three scalar resolvers."""

    x: Scalar
    y: Scalar
    z: Scalar

    def _decide(self) -> Vec3Decision:
        decided = gather([self.x.decide(), self.y.decide(), self.z.decide()])
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(as_vec3(np.array(decided.value, dtype=np.float64)))
