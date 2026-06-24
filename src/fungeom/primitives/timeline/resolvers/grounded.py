"""An instant placed on a (deferred) timeline, master-anchored on resolution.

This resolves to an :class:`~fungeom.primitives.instant.Instant`, but is built
from a :class:`~fungeom.primitives.timeline.Timeline` and so lives under
``timeline`` (which already depends on ``instant``; the reverse would be a cycle).
It mirrors ``FramedPoint3`` — local coordinates placed in a deferred frame.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.timeline.resolvers.base import Timeline


@dataclass(frozen=True, eq=False)
class GroundedInstant(Instant):
    """The instant at ``local`` seconds on ``timeline``.

    Resolvable iff both the timeline and the local time are; it resolves to the
    corresponding master-clock seconds. A detached (un-synced) timeline makes it
    Unresolvable — the local time has no master-clock meaning.
    """

    timeline: Timeline
    local: Scalar

    def _decide(self) -> InstantDecision:
        match self.timeline.decide(), self.local.decide():
            case Resolvable(clock), Resolvable(local):
                return Resolvable(clock.to_master().apply(local))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
