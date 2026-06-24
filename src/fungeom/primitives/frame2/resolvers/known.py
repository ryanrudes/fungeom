"""A resolver wrapping an already-known 2D coordinate frame."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.decidability import CoordinateFrame2Decision
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.frame2.value import CoordinateFrame2


@dataclass(frozen=True, eq=False)
class KnownFrame2(Frame2):
    """A leaf resolver for a literal :class:`CoordinateFrame2`.

    Resolvable iff the frame is grounded; resolves to its world-anchored form.
    """

    frame: CoordinateFrame2

    def _decide(self) -> CoordinateFrame2Decision:
        if not self.frame.is_grounded:
            return Unresolvable(f"frame {self.frame.name!r} is not grounded to the world")
        return Resolvable(self.frame.world())


def as_frame2(frame: CoordinateFrame2 | Frame2) -> Frame2:
    """Coerce a frame *value* into a resolver; pass frame resolvers through."""
    return frame if isinstance(frame, Frame2) else KnownFrame2(frame=frame)
