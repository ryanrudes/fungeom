"""A monotonic warp recovered from a sequence of correspondence knots."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timewarp.decidability import TimeWarpDecision
from fungeom.primitives.timewarp.resolvers.base import TimeWarp
from fungeom.primitives.timewarp.value import PiecewiseLinearWarp


def _strictly_increasing(xs: tuple[float, ...]) -> bool:
    return all(b > a for a, b in zip(xs, xs[1:]))


@dataclass(frozen=True, eq=False)
class ThroughTimeWarp(TimeWarp):
    """The piecewise-linear warp through ``(sources[i], targets[i])`` knots.

    Unresolvable unless there are at least two knots and both the source and target
    readings are strictly increasing — an order-preserving map is the defining
    invariant of a time warp.
    """

    sources: tuple[float, ...]
    targets: tuple[float, ...]

    def _decide(self) -> TimeWarpDecision:
        if len(self.sources) < 2:
            return Unresolvable("a time warp needs at least two correspondence knots")
        if not _strictly_increasing(self.sources):
            return Unresolvable("a time warp's source times must be strictly increasing")
        if not _strictly_increasing(self.targets):
            return Unresolvable("a time warp's target times must be strictly increasing")
        return Resolvable(PiecewiseLinearWarp(source=self.sources, target=self.targets))
