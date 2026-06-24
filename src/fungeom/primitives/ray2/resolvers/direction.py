"""A 2D ray's unit direction (→ Direction2)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.decidability import Direction2Decision
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.direction2.value import Direction2Value
from fungeom.primitives.ray2.resolvers.base import Ray2


@dataclass(frozen=True, eq=False)
class Ray2Direction(Direction2):
    """``ray``'s unit direction — total."""

    ray: Ray2

    def _decide(self) -> Direction2Decision:
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(Direction2Value(vector=ray.direction))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
