"""The coordinate frame *value*.

A :class:`CoordinateFrame` is a node in a tree of reference frames rooted at
:data:`WORLD_FRAME`. Each frame holds the rigid transform mapping its *own*
coordinates into its *parent's*; walking up the chain and composing gives the
frame-to-world transform. A frame whose chain reaches :data:`WORLD_FRAME` is
*grounded*; a detached one (a subassembly not yet placed) is not.

Frames are frozen dataclasses with identity equality: two frames are "the same
frame" only if they are the same object. The deferred counterpart — a
``Frame`` that resolves *to* a grounded ``CoordinateFrame`` —
lives in :mod:`fungeom.primitives.frame.resolvers`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fungeom.primitives.transform.value import RigidTransform


@dataclass(frozen=True, eq=False)
class CoordinateFrame:
    """A reference frame defined relative to a parent frame."""

    name: str
    parent: CoordinateFrame | None = None
    to_parent: RigidTransform = field(default_factory=RigidTransform.identity)
    """Transform mapping coordinates in *this* frame into ``parent``."""

    def to_world(self) -> RigidTransform:
        """Compose transforms up the parent chain to reach the world frame."""
        transform = self.to_parent
        frame = self.parent
        while frame is not None:
            transform = frame.to_parent @ transform
            frame = frame.parent
        return transform

    def transform_to(self, other: CoordinateFrame) -> RigidTransform:
        """The transform that re-expresses *this* frame's coordinates in ``other``."""
        return other.to_world().inverse() @ self.to_world()

    def child(self, name: str, to_parent: RigidTransform) -> CoordinateFrame:
        """Create a new frame that is a child of this one."""
        return CoordinateFrame(name=name, parent=self, to_parent=to_parent)

    @classmethod
    def detached(cls, name: str) -> CoordinateFrame:
        """A free frame whose placement in the world is not (yet) known.

        Its root is itself rather than :data:`WORLD_FRAME`, so it is *not*
        grounded — geometry expressed in it cannot be resolved to world
        coordinates until the frame is placed.
        """
        return cls(name=name, parent=None)

    @property
    def root(self) -> CoordinateFrame:
        """The frame at the top of this frame's parent chain."""
        frame = self
        while frame.parent is not None:
            frame = frame.parent
        return frame

    @property
    def is_grounded(self) -> bool:
        """Whether this frame's chain terminates at :data:`WORLD_FRAME`."""
        return self.root is WORLD_FRAME

    def world(self) -> CoordinateFrame:
        """An equivalent frame attached *directly* to :data:`WORLD_FRAME`.

        Flattens the parent chain into a single transform. Raises ``ValueError``
        if the frame is not grounded — go through a ``Frame``
        for a graceful answer.
        """
        if not self.is_grounded:
            raise ValueError(f"frame {self.name!r} is not grounded to the world")
        if self is WORLD_FRAME:
            return self
        return CoordinateFrame(name=self.name, parent=WORLD_FRAME, to_parent=self.to_world())

    def __repr__(self) -> str:
        parent = self.parent.name if self.parent is not None else None
        return f"CoordinateFrame(name={self.name!r}, parent={parent!r})"


WORLD_FRAME = CoordinateFrame(name="world", parent=None)
"""The root reference frame. All resolved geometry is expressed here."""
