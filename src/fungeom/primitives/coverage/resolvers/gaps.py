"""The gaps of a coverage — the holes between its spans, as another coverage."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.coverage.decidability import CoverageDecision
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue, gaps


@dataclass(frozen=True, eq=False)
class CoverageGaps(Coverage):
    """The complement of ``coverage`` within its own hull (empty if fewer than two spans)."""

    coverage: Coverage

    def _decide(self) -> CoverageDecision:
        match self.coverage.decide():
            case Resolvable(value):
                return Resolvable(CoverageValue(intervals=gaps(value.intervals)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
