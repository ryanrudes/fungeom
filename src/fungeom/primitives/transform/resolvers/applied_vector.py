"""A vector with a rigid transform applied (rotation only)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class TransformedVec3(Vec3):
    """``transform`` applied to a free ``vector`` — rotated, not translated.

    Resolvable iff both are: a rigid transform is always applicable.
    """

    transform: Transform
    vector: Vec3

    def _decide(self) -> Vec3Decision:
        match self.transform.decide(), self.vector.decide():
            case Resolvable(t), Resolvable(v):
                return Resolvable(t.apply_vector(v))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
