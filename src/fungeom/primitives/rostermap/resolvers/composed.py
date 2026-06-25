"""The composition of two roster maps."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.rostermap.decidability import RosterMapDecision
from fungeom.primitives.rostermap.resolvers.base import RosterMap


@dataclass(frozen=True, eq=False)
class ComposedRosterMap(RosterMap):
    """``outer ∘ inner`` — apply ``inner`` first, then ``outer``.

    Total: the result's source domain is just the subset of ``inner``'s sources whose
    target lands in ``outer``'s source domain (it may be empty).
    """

    outer: RosterMap
    inner: RosterMap

    def _decide(self) -> RosterMapDecision:
        match self.outer.decide(), self.inner.decide():
            case Resolvable(outer), Resolvable(inner):
                return Resolvable(outer.compose(inner))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
