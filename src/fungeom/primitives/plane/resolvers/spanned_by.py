"""A plane through a point spanned by two vectors — partial when they are parallel."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class PlaneSpannedBy(Plane):
    """The plane through ``anchor`` spanned by ``u`` and ``v`` (normal ``u × v``; Unresolvable if parallel)."""

    anchor: Point3
    u: Vec3
    v: Vec3

    def _decide(self) -> PlaneDecision:
        match self.anchor.decide(), self.u.decide(), self.v.decide():
            case (Resolvable(point), Resolvable(u), Resolvable(v)):
                normal = np.cross(u, v)
                if float(np.linalg.norm(normal)) == 0.0:
                    return Unresolvable("two parallel vectors do not span a plane")
                return Resolvable(PlaneValue(point=point.coord, normal=normal))
            case (Unresolvable() as bad, _, _):
                return bad
            case (_, Unresolvable() as bad, _):
                return bad
            case (_, _, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
