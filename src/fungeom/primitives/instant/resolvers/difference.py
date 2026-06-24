"""The duration spanning two instants.

This is a ``Duration`` (it resolves to an elapsed time), but it is built from
instants and so lives under ``instant``: ``instant`` already depends on
``duration``, and the reverse dependency would be a cycle. It mirrors
``DisplacementVec3`` (point − point → vector).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.resolvers.base import Instant


@dataclass(frozen=True, eq=False)
class InstantDuration(Duration):
    """The duration from ``earlier`` to ``later`` (``later - earlier``).

    A duration whose resolvability is *not* trivial: it inherits the
    resolvability of the two instants it spans.
    """

    later: Instant
    earlier: Instant

    def _decide(self) -> DurationDecision:
        match self.later.decide(), self.earlier.decide():
            case Resolvable(later), Resolvable(earlier):
                return Resolvable(later - earlier)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
