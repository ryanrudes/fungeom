"""A single component of a 3D vector, as a scalar."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class Vec3Coordinate(Scalar):
    """Component ``axis`` (0 = x, 1 = y, 2 = z) of ``vector`` — resolvable iff the vector is."""

    vector: Vec3
    axis: int

    def _decide(self) -> ScalarDecision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(float(decided.value[self.axis]))
