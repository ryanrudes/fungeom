"""A resolver wrapping an already-known clock."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timeline.decidability import TimelineDecision
from fungeom.primitives.timeline.resolvers.base import Timeline
from fungeom.primitives.timeline.value import Clock


@dataclass(frozen=True, eq=False)
class KnownTimeline(Timeline):
    """A leaf resolver for a literal :class:`Clock`.

    Resolvable iff the clock is grounded; resolves to its master-anchored form.
    """

    clock: Clock

    def _decide(self) -> TimelineDecision:
        if not self.clock.is_grounded:
            return Unresolvable(f"timeline {self.clock.name!r} is not synced to the master clock")
        return Resolvable(self.clock.grounded())
