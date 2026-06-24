"""Whether two intervals overlap — resolving to a ``Bool``.

Closed-interval semantics: spans that touch at a single instant *do* overlap
(consistent with :meth:`Interval.intersection`, which meets them in a degenerate
point rather than calling them disjoint).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.interval.resolvers.base import Interval


@dataclass(frozen=True, eq=False)
class IntervalOverlaps(Bool):
    """Whether ``a`` and ``b`` share any instant (``a.start ≤ b.end ∧ b.start ≤ a.end``)."""

    a: Interval
    b: Interval

    def _decide(self) -> BoolDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(x), Resolvable(y):
                return Resolvable(x.start <= y.end and y.start <= x.end)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
