"""A 2D ray reversed — the opposite half-line from the same origin."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.ray2.decidability import Ray2Decision
from fungeom.primitives.ray2.resolvers.base import Ray2


@dataclass(frozen=True, eq=False)
class Ray2Reversed(Ray2):
    """``ray`` with its direction negated (the same origin) — total."""

    ray: Ray2

    def _decide(self) -> Ray2Decision:
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(ray.reversed())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
