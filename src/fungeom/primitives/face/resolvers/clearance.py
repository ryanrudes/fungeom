"""The 3D distance from a point to a bounded patch (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class FaceClearance(Scalar):
    """The 3-D distance from ``point`` to the nearest point of ``face`` — Unresolvable if empty.

    The honest bounded-patch clearance: it clamps into the region first, so a foot beside the
    patch measures to its edge (not to the point directly below, as the infinite plane would).
    """

    face: Face
    point: Point3

    def _decide(self) -> ScalarDecision:
        match self.face.decide(), self.point.decide():
            case (Resolvable(face), Resolvable(point)):
                if face.region.is_empty:
                    return Unresolvable("the clearance to an empty face is undefined")
                return Resolvable(face.clearance(point.coord))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
