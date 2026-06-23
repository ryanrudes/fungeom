"""The Euclidean length of a 3D vector, as a scalar.

A ``Scalar`` built from a ``Vec3`` — so it lives under ``vec3``
(which already depends on ``scalar``), mirroring how ``DisplacementVec3`` lives
under ``point3``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class Vec3Norm(Scalar):
    """``‖vector‖`` — resolvable iff the vector is."""

    vector: Vec3

    def _decide(self) -> ScalarDecision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(float(np.linalg.norm(decided.value)))
