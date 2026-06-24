"""The affine map from a timeline's own seconds to the master clock's.

This resolves to a :class:`~fungeom.primitives.timemap.TimeMap`, but is built from
a :class:`~fungeom.primitives.timeline.Timeline` and so lives under ``timeline``
(which already depends on ``timemap``; the reverse would be a cycle). It is the
temporal mirror of ``Frame.relative_to(Frame.world)``.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timeline.resolvers.base import Timeline
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap


@dataclass(frozen=True, eq=False)
class TimelineToMaster(TimeMap):
    """The map taking ``timeline``'s local seconds into master-clock seconds.

    Resolvable iff the timeline is grounded — a detached (un-synced) clock has no
    master-clock relationship, so the map is undefined.
    """

    timeline: Timeline

    def _decide(self) -> TimeMapDecision:
        match self.timeline.decide():
            case Resolvable(clock):
                return Resolvable(clock.to_master())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
