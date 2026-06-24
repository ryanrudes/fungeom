"""The representative point of a plane (→ Point3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class PlaneOrigin(Point3):
    """The plane's representative (anchor) point, in the world frame."""

    plane: Plane

    def _decide(self) -> Point3Decision:
        match self.plane.decide():
            case Resolvable(value):
                return Resolvable(Point3Value(coord=value.point, frame=WORLD_FRAME))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
