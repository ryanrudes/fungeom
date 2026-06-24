"""The ``Timeline`` interface — clocks, grounding, and instants upon them.

A timeline is the temporal mirror of a :class:`~fungeom.Frame`: a clock grounded
to a chosen **master** clock through a chain of affine maps. Use :attr:`master`
(the root), :meth:`detached` (an un-synced clock), or :meth:`known`, and build
trees with :meth:`derive` — whose map *is* the sync/alignment relationship. An
instant placed on a detached timeline cannot be master-anchored and is
:class:`~fungeom.Unresolvable`, exactly as a point in a detached frame is. Sibling
resolver types are imported lazily to keep module load acyclic; the lower-layer
``Clock`` / ``AffineTimeMap`` are imported normally.
"""

from __future__ import annotations

from typing import ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.timeline.value import Clock
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap


class Timeline(Resolver[Clock]):
    """A deferred reference clock — a node in the tree of clocks.

    Use :attr:`master` (the root), :meth:`detached` (a clock not yet synced), or
    :meth:`known`, and build trees with :meth:`derive` (a child clock related to
    its parent by a :class:`~fungeom.TimeMap`). Place instants on it with
    :meth:`at`, and recover the relating maps with :meth:`to_master` /
    :meth:`relative_to` (→ ``TimeMap``). ``resolve()`` master-anchors the clock
    (flattening its chain to a single map off the master clock); a clock whose
    chain does not reach the master is :class:`~fungeom.Unresolvable`.

    Grounding *is* synchronization: a detached recording is an un-grounded
    timeline, and the :meth:`derive` map that places it relative to a grounded
    clock is exactly the alignment between the two.
    """

    type Value = Clock
    """The resolved value type — a master-grounded :class:`Clock`."""

    master: ClassVar[Timeline]
    """The root master clock, as a resolver. (Assigned once ``KnownTimeline`` exists.)"""

    @classmethod
    def known(cls, value: Clock) -> Timeline:
        """Wrap an already-known :class:`Clock` value."""
        from fungeom.primitives.timeline.resolvers.known import KnownTimeline

        return KnownTimeline(clock=value)

    @classmethod
    def detached(cls, name: str) -> Timeline:
        """A free clock not (yet) synced to the master — resolving it is Unresolvable."""
        from fungeom.primitives.timeline.resolvers.known import KnownTimeline

        return KnownTimeline(clock=Clock.detached(name))

    def derive(self, name: str, by: AffineTimeMap | TimeMap) -> Timeline:
        """A child clock related to this one ``by`` an affine map (possibly deferred)."""
        from fungeom.primitives.timeline.resolvers.derived import DerivedTimeline
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return DerivedTimeline(parent=self, name=name, by=as_timemap_resolver(by))

    def at(self, local: float | Scalar) -> Instant:
        """The instant at ``local`` seconds *on this clock*, master-anchored on resolution."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.timeline.resolvers.grounded import GroundedInstant

        return GroundedInstant(timeline=self, local=as_scalar_resolver(local))

    def to_master(self) -> TimeMap:
        """The :class:`~fungeom.TimeMap` from this clock's seconds to the master's.

        Unresolvable if this timeline is detached (not synced to the master) — the
        temporal mirror of ``Frame.relative_to(Frame.world)``.
        """
        from fungeom.primitives.timeline.resolvers.to_master import TimelineToMaster

        return TimelineToMaster(timeline=self)

    def relative_to(self, other: Timeline) -> TimeMap:
        """The :class:`~fungeom.TimeMap` re-expressing this clock's seconds in ``other``'s.

        Unresolvable if either timeline is ungrounded, or if ``other`` is a frozen
        (zero-rate) clock that cannot be inverted to serve as the reference.
        """
        from fungeom.primitives.timeline.resolvers.relative import TimelineRelativeTo

        return TimelineRelativeTo(timeline=self, other=other)
