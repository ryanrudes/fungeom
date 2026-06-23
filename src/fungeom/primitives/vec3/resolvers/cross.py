"""The cross product of two vectors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.value import as_vec3


@dataclass(frozen=True, eq=False)
class CrossVec3(Vec3):
    """``a × b`` — resolvable iff both vectors are."""

    a: Vec3
    b: Vec3

    def _decide(self) -> Vec3Decision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(as_vec3(np.cross(a, b)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
