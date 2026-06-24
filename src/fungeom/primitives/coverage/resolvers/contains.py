"""Membership of an instant in a coverage — resolving to a ``Bool``.

Resolves into a :class:`~fungeom.Bool` but is built from a ``Coverage`` and an
``Instant``, so it lives under ``coverage`` (which already depends on both).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.instant.resolvers.base import Instant


@dataclass(frozen=True, eq=False)
class CoverageContains(Bool):
    """Whether ``instant`` falls inside any span of ``coverage``."""

    coverage: Coverage
    instant: Instant

    def _decide(self) -> BoolDecision:
        match self.coverage.decide(), self.instant.decide():
            case Resolvable(cov), Resolvable(t):
                return Resolvable(any(span.start <= t <= span.end for span in cov.intervals))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
