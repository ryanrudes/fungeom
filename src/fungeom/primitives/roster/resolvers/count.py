"""The cardinality of a roster — resolving to a ``Scalar``.

The nominal-axis mirror of :class:`~fungeom.Coverage`'s ``total_duration``: a roster's
"measure" is its key count, not a summed length.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class RosterCount(Scalar):
    """How many keys are in ``roster`` — its cardinality (0 for the empty roster)."""

    roster: Roster

    def _decide(self) -> ScalarDecision:
        match self.roster.decide():
            case Resolvable(value):
                return Resolvable(float(len(value)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
