"""The point of a bounded patch nearest a query point (→ Point3, clamped into the region)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class FaceClosestPoint(Point3):
    """The point of ``face`` nearest ``point`` — clamped into the region; Unresolvable if empty."""

    face: Face
    point: Point3

    def _decide(self) -> Point3Decision:
        match self.face.decide(), self.point.decide():
            case (Resolvable(face), Resolvable(point)):
                if face.region.is_empty:
                    return Unresolvable("an empty face has no surface point")
                return Resolvable(Point3Value(coord=face.closest_point(point.coord), frame=WORLD_FRAME))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
