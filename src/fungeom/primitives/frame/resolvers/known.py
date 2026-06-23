"""A resolver wrapping an already-known coordinate frame."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.decidability import CoordinateFrameDecision
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.value import CoordinateFrame


@dataclass(frozen=True, eq=False)
class KnownFrame(Frame):
    """A leaf resolver for a literal :class:`CoordinateFrame`.

    Resolvable iff the frame is grounded; resolves to its world-anchored form.
    """

    frame: CoordinateFrame

    def _decide(self) -> CoordinateFrameDecision:
        if not self.frame.is_grounded:
            return Unresolvable(f"frame {self.frame.name!r} is not grounded to the world")
        return Resolvable(self.frame.world())


def as_frame(frame: CoordinateFrame | Frame) -> Frame:
    """Coerce a frame *value* into a resolver; pass frame resolvers through."""
    return frame if isinstance(frame, Frame) else KnownFrame(frame=frame)
