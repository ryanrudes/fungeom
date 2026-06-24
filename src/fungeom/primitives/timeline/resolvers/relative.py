"""The affine map re-expressing one timeline's seconds in another's.

The temporal mirror of ``Frame.relative_to``: it resolves to a
:class:`~fungeom.primitives.timemap.TimeMap` but is built from
:class:`~fungeom.primitives.timeline.Timeline`\\ s, so it lives under ``timeline``.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.timeline.resolvers.base import Timeline
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap


@dataclass(frozen=True, eq=False)
class TimelineRelativeTo(TimeMap):
    """The map taking ``timeline``'s local seconds into ``other``'s local seconds.

    Resolvable iff both timelines are grounded — *and* ``other`` is not a frozen
    (zero-rate) clock, since re-expressing into it requires inverting its
    master map. It is ``other.to_master⁻¹ ∘ this.to_master`` (this → master →
    other).
    """

    timeline: Timeline
    other: Timeline

    def _decide(self) -> TimeMapDecision:
        match self.timeline.decide(), self.other.decide():
            case Resolvable(this), Resolvable(other):
                target = other.to_master()
                if not target.is_invertible:
                    return Unresolvable(f"reference clock {other.name!r} is frozen (zero rate) and cannot be inverted")
                return Resolvable(target.inverse().compose(this.to_master()))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
