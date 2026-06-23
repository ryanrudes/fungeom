"""The ``Frame`` interface."""

from __future__ import annotations

from typing import ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.frame.value import CoordinateFrame
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform


class Frame(Resolver[CoordinateFrame]):
    """A deferred coordinate frame — a node in the tree of reference frames.

    Use :attr:`world` (the root), :meth:`detached` (a frame not yet placed), or
    :meth:`known` (wrapping a :class:`~fungeom.CoordinateFrame` value), and
    build trees with :meth:`attach`. ``resolve()`` world-anchors the frame
    (flattening its chain to a single transform off the world frame); a frame
    whose chain does not reach the world is
    :class:`~fungeom.Unresolvable` — see :meth:`decide`.
    """

    type Value = CoordinateFrame
    """The resolved value type — a :class:`CoordinateFrame`."""

    world: ClassVar[Frame]
    """The root world frame, as a resolver. (Assigned once ``KnownFrame`` exists.)"""

    @classmethod
    def known(cls, value: CoordinateFrame) -> Frame:
        """Wrap an already-known :class:`CoordinateFrame` value."""
        from fungeom.primitives.frame.resolvers.known import KnownFrame

        return KnownFrame(frame=value)

    @classmethod
    def detached(cls, name: str) -> Frame:
        """A free frame not (yet) grounded to the world — resolving it is Unresolvable."""
        from fungeom.primitives.frame.resolvers.known import KnownFrame

        return KnownFrame(frame=CoordinateFrame.detached(name))

    def attach(self, name: str, to_parent: RigidTransform | Transform) -> Frame:
        """A child frame placed ``to_parent`` (a transform, possibly deferred) relative to this one."""
        from fungeom.primitives.frame.resolvers.attached import AttachedFrame
        from fungeom.primitives.transform.resolvers.literal import as_transform_resolver

        return AttachedFrame(parent=self, name=name, to_parent=as_transform_resolver(to_parent))
