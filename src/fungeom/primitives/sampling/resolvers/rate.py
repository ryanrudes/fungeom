"""The average sample rate (Hz) of a sampling — partial below two samples."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class SamplingRate(Scalar):
    """The mean rate ``(count - 1) / (last - first)`` in Hz.

    Unresolvable for a sampling with fewer than two samples — a single instant
    spans no time, so it defines no rate. (Two or more are guaranteed strictly
    increasing, so the span is positive and the division is safe.)
    """

    sampling: Sampling

    def _decide(self) -> ScalarDecision:
        match self.sampling.decide():
            case Resolvable(base):
                if base.count < 2:
                    return Unresolvable("rate of a sampling with fewer than two samples is undefined")
                span = float(base.times[-1] - base.times[0])
                return Resolvable((base.count - 1) / span)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
