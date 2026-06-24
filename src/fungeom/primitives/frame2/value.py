"""The 2D coordinate frame *value*.

A :class:`CoordinateFrame2` is the planar sibling of
:class:`~fungeom.values.CoordinateFrame` — a node in a tree of 2D reference frames
rooted at :data:`WORLD_FRAME2`. Each frame holds the rigid 2D transform mapping its
*own* coordinates into its *parent's*; walking up the chain and composing gives the
frame-to-world transform. A frame whose chain reaches :data:`WORLD_FRAME2` is
*grounded*; a detached one is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fungeom.primitives.transform2.value import RigidTransform2


@dataclass(frozen=True, eq=False)
class CoordinateFrame2:
    """A 2D reference frame defined relative to a parent frame."""

    name: str
    parent: CoordinateFrame2 | None = None
    to_parent: RigidTransform2 = field(default_factory=RigidTransform2.identity)
    """Transform mapping coordinates in *this* frame into ``parent``."""

    def to_world(self) -> RigidTransform2:
        """Compose transforms up the parent chain to reach the world frame."""
        transform = self.to_parent
        frame = self.parent
        while frame is not None:
            transform = frame.to_parent @ transform
            frame = frame.parent
        return transform

    def transform_to(self, other: CoordinateFrame2) -> RigidTransform2:
        """The transform that re-expresses *this* frame's coordinates in ``other``."""
        return other.to_world().inverse() @ self.to_world()

    def child(self, name: str, to_parent: RigidTransform2) -> CoordinateFrame2:
        """Create a new frame that is a child of this one."""
        return CoordinateFrame2(name=name, parent=self, to_parent=to_parent)

    @classmethod
    def detached(cls, name: str) -> CoordinateFrame2:
        """A free frame whose placement in the world is not (yet) known (its root is itself)."""
        return cls(name=name, parent=None)

    @property
    def root(self) -> CoordinateFrame2:
        """The frame at the top of this frame's parent chain."""
        frame = self
        while frame.parent is not None:
            frame = frame.parent
        return frame

    @property
    def is_grounded(self) -> bool:
        """Whether this frame's chain terminates at :data:`WORLD_FRAME2`."""
        return self.root is WORLD_FRAME2

    def world(self) -> CoordinateFrame2:
        """An equivalent frame attached *directly* to :data:`WORLD_FRAME2` (chain flattened).

        Raises ``ValueError`` if the frame is not grounded — go through a ``Frame2`` for a
        graceful answer.
        """
        if not self.is_grounded:
            raise ValueError(f"frame {self.name!r} is not grounded to the world")
        if self is WORLD_FRAME2:
            return self
        return CoordinateFrame2(name=self.name, parent=WORLD_FRAME2, to_parent=self.to_world())

    def __repr__(self) -> str:
        parent = self.parent.name if self.parent is not None else None
        return f"CoordinateFrame2(name={self.name!r}, parent={parent!r})"


WORLD_FRAME2 = CoordinateFrame2(name="world2", parent=None)
"""The root 2D reference frame. All resolved planar geometry is expressed here."""
