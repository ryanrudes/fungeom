"""The timeline *value*: a clock in the tree of reference clocks.

A :class:`Clock` is a node in a tree rooted at :data:`MASTER_CLOCK`, the temporal
mirror of :data:`~fungeom.primitives.frame.value.WORLD_FRAME`. Each clock holds
the affine map taking its *own* seconds into its *parent's*; composing up the
chain gives the clock-to-master map. A clock whose chain reaches
:data:`MASTER_CLOCK` is *grounded*; a detached one (an un-synced recording) is not,
exactly as a detached coordinate frame is not grounded to the world.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fungeom.primitives.timemap.value import AffineTimeMap


@dataclass(frozen=True, eq=False)
class Clock:
    """A reference clock defined relative to a parent clock."""

    name: str
    parent: Clock | None = None
    to_parent: AffineTimeMap = field(default_factory=AffineTimeMap.identity)
    """Affine map taking *this* clock's seconds into ``parent``."""

    def to_master(self) -> AffineTimeMap:
        """Compose affine maps up the parent chain to reach the master clock."""
        timemap = self.to_parent
        clock = self.parent
        while clock is not None:
            timemap = clock.to_parent.compose(timemap)
            clock = clock.parent
        return timemap

    def child(self, name: str, to_parent: AffineTimeMap) -> Clock:
        """Create a new clock that is a child of this one."""
        return Clock(name=name, parent=self, to_parent=to_parent)

    @classmethod
    def detached(cls, name: str) -> Clock:
        """A free clock whose relationship to the master clock is not (yet) known.

        Its root is itself rather than :data:`MASTER_CLOCK`, so it is *not*
        grounded — instants on it cannot be resolved to master-clock seconds until
        the clock is synced.
        """
        return cls(name=name, parent=None)

    @property
    def root(self) -> Clock:
        """The clock at the top of this clock's parent chain."""
        clock = self
        while clock.parent is not None:
            clock = clock.parent
        return clock

    @property
    def is_grounded(self) -> bool:
        """Whether this clock's chain terminates at :data:`MASTER_CLOCK`."""
        return self.root is MASTER_CLOCK

    def grounded(self) -> Clock:
        """An equivalent clock attached *directly* to :data:`MASTER_CLOCK`.

        Flattens the parent chain into a single map. Raises ``ValueError`` if the
        clock is not grounded — go through a ``Timeline`` for a graceful answer.
        """
        if not self.is_grounded:
            raise ValueError(f"clock {self.name!r} is not grounded to the master clock")
        if self is MASTER_CLOCK:
            return self
        return Clock(name=self.name, parent=MASTER_CLOCK, to_parent=self.to_master())

    def __repr__(self) -> str:
        parent = self.parent.name if self.parent is not None else None
        return f"Clock(name={self.name!r}, parent={parent!r})"


MASTER_CLOCK = Clock(name="master", parent=None)
"""The root reference clock. All resolved instants are expressed in its seconds."""
