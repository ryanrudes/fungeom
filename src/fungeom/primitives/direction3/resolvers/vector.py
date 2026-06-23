"""A direction viewed as a (unit) vector.

A ``Vec3`` built from a ``Direction3`` — so it lives under
``direction3`` (which already depends on ``vec3``), letting a direction be used
anywhere a vector is expected.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class DirectionVec3(Vec3):
    """The unit vector of ``direction`` — resolvable iff ``direction`` is."""

    direction: Direction3

    def _decide(self) -> Vec3Decision:
        decided = self.direction.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(decided.value.vector)
