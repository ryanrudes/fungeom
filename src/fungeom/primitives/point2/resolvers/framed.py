"""A 2D point at (deferred) local coordinates in a (deferred) frame."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class FramedPoint2(Point2):
    """Local coordinates ``local`` expressed in the deferred frame ``frame`` — resolvable iff both are."""

    local: Vec2
    frame: Frame2

    def _decide(self) -> Point2Decision:
        match self.frame.decide(), self.local.decide():
            case Resolvable(frame), Resolvable(local):
                # The resolved frame is already world-grounded.
                return Resolvable(Point2Value(coord=local, frame=frame).world())
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
