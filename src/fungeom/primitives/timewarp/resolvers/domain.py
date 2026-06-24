"""The closed source span a time warp is defined over."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.timewarp.resolvers.base import TimeWarp


@dataclass(frozen=True, eq=False)
class WarpDomain(Interval):
    """``[first source knot, last source knot]`` — the span over which ``warp`` maps.

    Total (a valid warp has at least two strictly-increasing knots, so the span
    exists); useful to check, as a graph node, that a warp covers a signal's time
    base before reparameterizing it.
    """

    warp: TimeWarp

    def _decide(self) -> IntervalDecision:
        match self.warp.decide():
            case Resolvable(value):
                lo, hi = value.domain
                return Resolvable(IntervalValue(start=lo, end=hi))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
