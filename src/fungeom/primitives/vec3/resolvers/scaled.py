"""A vector multiplied by a (deferred) scalar."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class ScaledVec3(Vec3):
    """``vector * factor`` — resolvable iff both the vector and the factor are."""

    vector: Vec3
    factor: Scalar

    def _decide(self) -> Vec3Decision:
        match self.vector.decide(), self.factor.decide():
            case Resolvable(vector), Resolvable(factor):
                return Resolvable(vector * factor)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
