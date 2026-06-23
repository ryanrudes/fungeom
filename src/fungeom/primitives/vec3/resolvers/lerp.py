"""Linear interpolation between two vectors."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class LerpVec3(Vec3):
    """``(1 - t) * a + t * b`` — resolvable iff both vectors and ``t`` are."""

    a: Vec3
    b: Vec3
    t: Scalar

    def _decide(self) -> Vec3Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(a), Resolvable(b), Resolvable(t):
                return Resolvable(a * (1.0 - t) + b * t)
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
