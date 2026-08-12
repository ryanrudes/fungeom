"""A uniform grid given as a rate and a count — partial when the rate is not positive."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.sampling.decidability import SamplingDecision
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.sampling.value import SamplingValue, monotonic_reason
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class PacedSampling(Sampling):
    """``samples`` instants from ``start_at``, one every ``1 / rate_hz`` seconds.

    The same grid :class:`~fungeom.primitives.sampling.resolvers.uniform.UniformSampling`
    describes, parameterized the way discrete data actually arrives: a rate and a number
    of samples, rather than the span they happen to cover.

    Unresolvable when ``samples`` is below 1, when either input is unresolvable, when the
    rate is not positive (zero, negative, or NaN — none of them define a spacing), or when
    the rate is so large that ``1 / rate_hz`` underflows and the grid stops increasing.

    The fields are ``start_at`` / ``rate_hz`` / ``samples`` so they do not shadow the
    facade's :meth:`Sampling.span`, :meth:`Sampling.rate` and :meth:`Sampling.count`
    methods — a concrete resolver subclasses its facade.
    """

    start_at: Instant
    rate_hz: Scalar
    samples: int

    def _decide(self) -> SamplingDecision:
        if self.samples < 1:
            return Unresolvable(f"a sampling needs at least 1 time, got {self.samples}")
        match self.start_at.decide(), self.rate_hz.decide():
            case Resolvable(start), Resolvable(rate):
                if not rate > 0.0:
                    return Unresolvable(f"a sampling rate must be positive, got {rate:g} Hz")
                times = start + np.arange(self.samples, dtype=np.float64) / rate
                reason = monotonic_reason(times)
                if reason is not None:
                    return Unresolvable(reason)
                return Resolvable(SamplingValue(times=times))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
