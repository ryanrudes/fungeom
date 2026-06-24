"""The closed interval spanned by a sampling's first and last instants."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.sampling.resolvers.base import Sampling


@dataclass(frozen=True, eq=False)
class SamplingSpan(Interval):
    """``[first, last]`` of the sampling — total (a valid sampling is non-empty, so the span exists)."""

    sampling: Sampling

    def _decide(self) -> IntervalDecision:
        match self.sampling.decide():
            case Resolvable(base):
                return Resolvable(IntervalValue(start=float(base.times[0]), end=float(base.times[-1])))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
