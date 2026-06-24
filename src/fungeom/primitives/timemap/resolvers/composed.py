"""The composition of two time maps."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap


@dataclass(frozen=True, eq=False)
class ComposedTimeMap(TimeMap):
    """``outer ∘ inner`` — apply ``inner`` first, then ``outer``."""

    outer: TimeMap
    inner: TimeMap

    def _decide(self) -> TimeMapDecision:
        match self.outer.decide(), self.inner.decide():
            case Resolvable(outer), Resolvable(inner):
                return Resolvable(outer.compose(inner))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
