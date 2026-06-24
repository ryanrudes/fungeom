"""The set difference of two coverages."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.coverage.decidability import CoverageDecision
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue, subtract


@dataclass(frozen=True, eq=False)
class CoverageDifference(Coverage):
    """Everything covered by ``a`` but not ``b`` (total — empty when ``b`` swallows ``a``)."""

    a: Coverage
    b: Coverage

    def _decide(self) -> CoverageDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(CoverageValue(intervals=subtract(a.intervals, b.intervals)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
