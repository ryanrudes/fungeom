"""The number of samples in a sampling, as a scalar."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class SamplingCount(Scalar):
    """The sample count of the sampling — total (a valid sampling has at least one time)."""

    sampling: Sampling

    def _decide(self) -> ScalarDecision:
        match self.sampling.decide():
            case Resolvable(base):
                return Resolvable(float(base.count))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
