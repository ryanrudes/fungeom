"""The ``Frame2`` interface — the 2D sibling of ``Frame``."""

from __future__ import annotations

from typing import ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.frame2.value import CoordinateFrame2
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.transform2.value import RigidTransform2


class Frame2(Resolver[CoordinateFrame2]):
    """A deferred 2D coordinate frame — a node in the tree of planar reference frames.

    Use :attr:`world` (the root), :meth:`detached` (a frame not yet placed), or
    :meth:`known` (wrapping a :class:`~fungeom.CoordinateFrame2` value), and build trees
    with :meth:`attach`; :meth:`relative_to` gives the 2D transform between two frames.
    ``resolve()`` world-anchors the frame (flattening its chain to a single transform off
    the world frame); a frame whose chain does not reach the world is
    :class:`~fungeom.Unresolvable`.
    """

    type Value = CoordinateFrame2
    """The resolved value type — a :class:`CoordinateFrame2`."""

    world: ClassVar[Frame2]
    """The root world frame, as a resolver. (Assigned once ``KnownFrame2`` exists.)"""

    @classmethod
    def known(cls, value: CoordinateFrame2) -> Frame2:
        """Wrap an already-known :class:`CoordinateFrame2` value."""
        from fungeom.primitives.frame2.resolvers.known import KnownFrame2

        return KnownFrame2(frame=value)

    @classmethod
    def detached(cls, name: str) -> Frame2:
        """A free frame not (yet) grounded to the world — resolving it is Unresolvable."""
        from fungeom.primitives.frame2.resolvers.known import KnownFrame2

        return KnownFrame2(frame=CoordinateFrame2.detached(name))

    def attach(self, name: str, to_parent: RigidTransform2 | Transform2) -> Frame2:
        """A child frame placed ``to_parent`` (a transform, possibly deferred) relative to this one."""
        from fungeom.primitives.frame2.resolvers.attached import AttachedFrame2
        from fungeom.primitives.transform2.resolvers.literal import as_transform2_resolver

        return AttachedFrame2(parent=self, name=name, to_parent=as_transform2_resolver(to_parent))

    def relative_to(self, other: Frame2) -> Transform2:
        """The transform re-expressing this frame's coordinates in ``other`` (Unresolvable if either is ungrounded)."""
        from fungeom.primitives.frame2.resolvers.relative import Frame2Transform

        return Frame2Transform(frame=self, other=other)
