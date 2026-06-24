"""A sampling at explicit timestamps — partial when they are not strictly increasing."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.sampling.decidability import SamplingDecision
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.sampling.value import SamplingValue, as_times, monotonic_reason


@dataclass(frozen=True, eq=False)
class ExplicitSampling(Sampling):
    """A sampling at the literal ``times``.

    Unresolvable when the times are empty or not strictly increasing — a corrupt
    capture (duplicate or out-of-order timestamps) defines no function of time.
    """

    times: tuple[float, ...]

    def _decide(self) -> SamplingDecision:
        times = as_times(self.times)
        reason = monotonic_reason(times)
        if reason is not None:
            return Unresolvable(reason)
        return Resolvable(SamplingValue(times=times))
