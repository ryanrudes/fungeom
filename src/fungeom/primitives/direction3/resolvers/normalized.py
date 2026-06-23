"""The direction of a (deferred) vector — partial at the origin.

The bridge from vectors to directions: turns a ``Vec3`` into a unit
``Direction3Value``. Unresolvable for the zero vector, which has no direction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class NormalizedDirection3(Direction3):
    """The direction of ``vector`` — Unresolvable for the zero vector."""

    vector: Vec3

    def _decide(self) -> Direction3Decision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        if float(np.linalg.norm(decided.value)) == 0.0:
            return Unresolvable("cannot take the direction of the zero vector")
        return Resolvable(Direction3Value(vector=decided.value))


def as_direction(vector: Vec3) -> Direction3:
    """The direction of a (deferred) vector."""
    return NormalizedDirection3(vector=vector)
