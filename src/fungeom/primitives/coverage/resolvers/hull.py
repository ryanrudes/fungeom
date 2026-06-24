"""The bounding interval of a coverage — partial when the coverage is empty.

This resolves to an :class:`~fungeom.primitives.interval.Interval`, but is built
from a :class:`~fungeom.primitives.coverage.Coverage` and so lives under
``coverage`` (which already depends on ``interval``; the reverse would be a cycle).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue


@dataclass(frozen=True, eq=False)
class CoverageHull(Interval):
    """The smallest interval containing every span of ``coverage``.

    Unresolvable when the coverage is empty — there is no interval to bound.
    """

    coverage: Coverage

    def _decide(self) -> IntervalDecision:
        match self.coverage.decide():
            case Resolvable(value):
                if value.is_empty:
                    return Unresolvable("hull of an empty coverage is undefined")
                return Resolvable(IntervalValue(start=value.intervals[0].start, end=value.intervals[-1].end))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
