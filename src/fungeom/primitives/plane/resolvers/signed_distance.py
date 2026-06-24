"""Signed distance from a point to a plane (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class PlaneSignedDistance(Scalar):
    """The signed distance from ``point`` to ``plane`` — total (positive on the normal side)."""

    plane: Plane
    point: Point3

    def _decide(self) -> ScalarDecision:
        match self.plane.decide(), self.point.decide():
            case Resolvable(plane), Resolvable(point):
                return Resolvable(plane.signed_distance(point.coord))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
