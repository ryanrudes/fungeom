"""A ray's unit direction (→ Direction3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.ray.resolvers.base import Ray


@dataclass(frozen=True, eq=False)
class RayDirection(Direction3):
    """``ray``'s unit direction — total (a ray always has one)."""

    ray: Ray

    def _decide(self) -> Direction3Decision:
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(Direction3Value(vector=ray.direction))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
