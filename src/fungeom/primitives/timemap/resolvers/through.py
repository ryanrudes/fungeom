"""A time map recovered exactly from two landmark correspondences (offset + rate)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap


@dataclass(frozen=True, eq=False)
class ThroughTimeMap(TimeMap):
    """The exact affine map through two correspondences ``s0 ↦ t0`` and ``s1 ↦ t1``.

    Two sync points determine both the offset and the rate (drift) — the clapper at
    the start *and* the end. The map is ``rate = (t1 − t0)/(s1 − s0)``,
    ``offset = t0 − rate · s0``. **Unresolvable** when the two source readings
    coincide (``s0 = s1``): the correspondences then constrain a single instant and
    leave the rate undetermined — the temporal mirror of fitting a line to one point.
    """

    source0: Scalar
    target0: Scalar
    source1: Scalar
    target1: Scalar

    def _decide(self) -> TimeMapDecision:
        match self.source0.decide(), self.target0.decide(), self.source1.decide(), self.target1.decide():
            case Resolvable(s0), Resolvable(t0), Resolvable(s1), Resolvable(t1):
                if s0 == s1:
                    return Unresolvable("the two correspondences share a source time, so the rate is undetermined")
                rate = (t1 - t0) / (s1 - s0)
                return Resolvable(AffineTimeMap(offset=t0 - rate * s0, rate=rate))
            case Unresolvable() as bad, _, _, _:
                return bad
            case _, (Unresolvable() as bad), _, _:
                return bad
            case _, _, (Unresolvable() as bad), _:
                return bad
            case _, _, _, (Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
