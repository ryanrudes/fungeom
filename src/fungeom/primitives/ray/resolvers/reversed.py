"""A ray reversed — the opposite half-line from the same origin."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.ray.decidability import RayDecision
from fungeom.primitives.ray.resolvers.base import Ray


@dataclass(frozen=True, eq=False)
class RayReversed(Ray):
    """``ray`` with its direction negated (the same origin) — total."""

    ray: Ray

    def _decide(self) -> RayDecision:
        match self.ray.decide():
            case Resolvable(ray):
                return Resolvable(ray.reversed())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
