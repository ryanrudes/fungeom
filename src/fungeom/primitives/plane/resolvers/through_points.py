"""A plane through three points — partial when they are collinear."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class PlaneThroughPoints(Plane):
    """The plane through ``a``, ``b``, ``c`` (normal ``(b - a) × (c - a)``; Unresolvable if collinear)."""

    a: Point3
    b: Point3
    c: Point3

    def _decide(self) -> PlaneDecision:
        decided = gather((self.a.decide(), self.b.decide(), self.c.decide()))
        if isinstance(decided, Unresolvable):
            return decided
        pa, pb, pc = (point.coord for point in decided.value)
        normal = np.cross(pb - pa, pc - pa)
        if float(np.linalg.norm(normal)) == 0.0:
            return Unresolvable("three collinear points do not define a plane")
        return Resolvable(PlaneValue(point=pa, normal=normal))
