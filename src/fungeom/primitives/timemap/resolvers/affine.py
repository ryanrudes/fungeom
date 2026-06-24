"""A time map assembled from a (deferred) offset and rate."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap


@dataclass(frozen=True, eq=False)
class AffineTimeMapResolver(TimeMap):
    """The map ``offset + rate · t`` — resolvable iff both the offset and rate are."""

    offset: Duration
    rate_factor: Scalar

    def _decide(self) -> TimeMapDecision:
        match self.offset.decide(), self.rate_factor.decide():
            case Resolvable(offset), Resolvable(rate):
                return Resolvable(AffineTimeMap(offset=offset, rate=rate))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
