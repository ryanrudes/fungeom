"""A 2D chart coordinate lifted onto the plane in world space (→ Point3) — the 2D→3D bridge."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class PlaneEmbed(Point3):
    """The world point at chart coordinates ``local`` on ``plane`` — the inverse of :class:`PlaneToLocal`.

    Lifts a 2D region's vertices/samples back to 3D: ``origin + u·x + v·y`` in the plane's
    deterministic basis. Resolvable whenever the plane and the 2D point are.
    """

    plane: Plane
    local: Point2

    def _decide(self) -> Point3Decision:
        match self.plane.decide(), self.local.decide():
            case (Resolvable(plane), Resolvable(local)):
                return Resolvable(Point3Value(coord=plane.embed(local.coord), frame=WORLD_FRAME))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
