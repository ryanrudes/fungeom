"""The summed length of a coverage, as a deferred ``Duration``.

This resolves to a :class:`~fungeom.primitives.duration.Duration`, but is built
from a :class:`~fungeom.primitives.coverage.Coverage` and so lives under
``coverage`` (which already depends on ``duration``; the reverse would be a cycle).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration


@dataclass(frozen=True, eq=False)
class CoverageTotalDuration(Duration):
    """The total covered time of ``coverage`` (zero for empty coverage)."""

    coverage: Coverage

    def _decide(self) -> DurationDecision:
        match self.coverage.decide():
            case Resolvable(value):
                return Resolvable(value.total_duration)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
