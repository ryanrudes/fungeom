"""The inverse of a time map — partial when the rate is zero."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap


@dataclass(frozen=True, eq=False)
class InverseTimeMap(TimeMap):
    """The inverse of ``timemap``.

    Unresolvable when the map's rate is zero — a frozen clock collapses every time
    to a single instant and so has no inverse.
    """

    timemap: TimeMap

    def _decide(self) -> TimeMapDecision:
        match self.timemap.decide():
            case Resolvable(value):
                if not value.is_invertible:
                    return Unresolvable("a time map with zero rate is not invertible")
                return Resolvable(value.inverse())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
