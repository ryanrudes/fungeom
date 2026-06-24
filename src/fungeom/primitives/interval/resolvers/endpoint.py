"""The endpoints of an interval, each a deferred ``Instant``.

These resolve to an :class:`~fungeom.primitives.instant.Instant`, but are built
from an :class:`~fungeom.primitives.interval.Interval` and so live under
``interval`` (which already depends on ``instant``; the reverse would be a cycle).
They mirror ``Vec3Coordinate`` (a scalar component extracted from a vector).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval


@dataclass(frozen=True, eq=False)
class IntervalStart(Instant):
    """The starting instant of ``interval``."""

    interval: Interval

    def _decide(self) -> InstantDecision:
        match self.interval.decide():
            case Resolvable(span):
                return Resolvable(span.start)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class IntervalEnd(Instant):
    """The ending instant of ``interval``."""

    interval: Interval

    def _decide(self) -> InstantDecision:
        match self.interval.decide():
            case Resolvable(span):
                return Resolvable(span.end)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
