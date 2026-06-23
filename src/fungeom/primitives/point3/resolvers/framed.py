"""A point at (deferred) local coordinates in a (deferred) frame.

The fully consistent point leaf: where ``LocatedPoint3`` wraps a concrete point
in a concrete frame, this places a *vector resolver* in a *frame resolver* — so a
point can sit in a frame that is itself still being resolved. Resolvable iff both
the frame and the local coordinates are.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class FramedPoint3(Point3):
    """Local coordinates ``local`` expressed in the deferred frame ``frame``."""

    local: Vec3
    frame: Frame

    def _decide(self) -> Point3Decision:
        match self.frame.decide(), self.local.decide():
            case Resolvable(frame), Resolvable(local):
                # The resolved frame is already world-grounded.
                return Resolvable(Point3Value(coord=local, frame=frame).world())
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
