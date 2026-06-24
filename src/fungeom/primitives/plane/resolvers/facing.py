"""Orient a plane's normal toward a point — partial when the point is on the plane."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class PlaneFacing(Plane):
    """``plane`` with its normal flipped to point toward ``point``'s halfspace.

    Resolves the unsure sign of a fitted plane's normal. Unresolvable when ``point``
    lies *on* the plane — its halfspace, and so the sign, is undefined.
    """

    plane: Plane
    point: Point3

    def _decide(self) -> PlaneDecision:
        match self.plane.decide(), self.point.decide():
            case Resolvable(plane), Resolvable(point):
                signed = plane.signed_distance(point.coord)
                if signed == 0.0:
                    return Unresolvable("the point lies on the plane, so the normal's outward side is undefined")
                return Resolvable(plane if signed > 0.0 else plane.flipped())
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
