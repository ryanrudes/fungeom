"""A 3D vector rescaled to a given length — partial at the origin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class ResizedVec3(Vec3):
    """``vector`` rescaled to length ``length`` while keeping its direction.

    Unresolvable for the zero vector — it has no direction to give a length to.
    """

    vector: Vec3
    length: Scalar

    def _decide(self) -> Vec3Decision:
        match self.vector.decide(), self.length.decide():
            case Resolvable(v), Resolvable(length):
                norm = float(np.linalg.norm(v))
                if norm == 0.0:
                    return Unresolvable("cannot give the zero vector a length")
                return Resolvable(v / norm * length)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
