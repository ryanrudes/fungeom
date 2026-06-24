"""The inverse of a time warp — total apart from propagation."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timewarp.decidability import TimeWarpDecision
from fungeom.primitives.timewarp.resolvers.base import TimeWarp


@dataclass(frozen=True, eq=False)
class InverseTimeWarp(TimeWarp):
    """The inverse of ``warp`` (target → source).

    A warp is strictly monotonic by construction, so its inverse always exists; this
    is Unresolvable only when ``warp`` itself is.
    """

    warp: TimeWarp

    def _decide(self) -> TimeWarpDecision:
        match self.warp.decide():
            case Resolvable(value):
                return Resolvable(value.inverse())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
