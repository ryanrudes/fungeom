"""A uniform sampling grid over an interval."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.sampling.decidability import SamplingDecision
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.sampling.value import SamplingValue, monotonic_reason


@dataclass(frozen=True, eq=False)
class UniformSampling(Sampling):
    """``samples`` evenly-spaced instants spanning ``over``.

    Unresolvable when ``samples`` is below 1, when the interval is unresolvable, or
    when the grid is not strictly increasing (e.g. more than one sample over a
    zero-length interval).

    The field is ``samples`` (not ``count``) so it does not shadow the facade's
    :meth:`Sampling.count` method — a concrete resolver subclasses its facade.
    """

    over: Interval
    samples: int

    def _decide(self) -> SamplingDecision:
        if self.samples < 1:
            return Unresolvable(f"a sampling needs at least 1 time, got {self.samples}")
        match self.over.decide():
            case Resolvable(span):
                times = np.linspace(span.start, span.end, self.samples, dtype=np.float64)
                reason = monotonic_reason(times)
                if reason is not None:
                    return Unresolvable(reason)
                return Resolvable(SamplingValue(times=times))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
