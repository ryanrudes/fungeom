"""The sum of two vectors."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class SumVec3(Vec3):
    """``a + b`` — resolvable iff both addends are."""

    a: Vec3
    b: Vec3

    def _decide(self) -> Vec3Decision:
        match self.a.decide(), self.b.decide():
            case Resolvable(va), Resolvable(vb):
                return Resolvable(va + vb)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
