"""A clock placed relative to another (deferred) clock by a (deferred) time map."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timeline.decidability import TimelineDecision
from fungeom.primitives.timeline.resolvers.base import Timeline
from fungeom.primitives.timemap.resolvers.base import TimeMap


@dataclass(frozen=True, eq=False)
class DerivedTimeline(Timeline):
    """A child clock related to ``parent`` ``by`` an affine map.

    Both the parent clock *and* the relating map are deferred, so this is
    resolvable iff both are; it resolves to the master-anchored child.
    """

    parent: Timeline
    name: str
    by: TimeMap

    def _decide(self) -> TimelineDecision:
        match self.parent.decide(), self.by.decide():
            case Resolvable(parent), Resolvable(by):
                return Resolvable(parent.child(self.name, by).grounded())
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
