"""Whether a 3D point projects into a bounded patch's footprint (→ Bool)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class FaceContains(Bool):
    """Whether ``point`` projects into ``face``'s footprint (the region contains its in-plane
    projection) — the support-polygon membership test, independent of the normal offset. Total
    (``False`` for an empty face).
    """

    face: Face
    point: Point3

    def _decide(self) -> BoolDecision:
        match self.face.decide(), self.point.decide():
            case (Resolvable(face), Resolvable(point)):
                return Resolvable(face.contains(point.coord))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
