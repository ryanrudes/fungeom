"""Where a ray meets a plane (→ Point3) — the raycast; partial when there is no forward hit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.ray.resolvers.base import Ray


@dataclass(frozen=True, eq=False)
class RayPlaneIntersection(Point3):
    """The point where ``ray`` first meets ``plane`` (→ ``Point3``).

    Solves ``t = (planePoint − origin) · normal / (direction · normal)``. **Unresolvable**
    when the ray is parallel to the plane (``direction · normal == 0`` — no unique hit, or
    the ray lies in the plane) or when the hit is behind the origin (``t < 0`` — the ray
    points away from the plane).
    """

    ray: Ray
    plane: Plane

    def _decide(self) -> Point3Decision:
        match self.ray.decide(), self.plane.decide():
            case Resolvable(ray), Resolvable(plane):
                denominator = float(np.dot(ray.direction, plane.normal))
                if denominator == 0.0:
                    return Unresolvable("the ray is parallel to the plane; there is no unique intersection")
                t = float(np.dot(plane.point - ray.point, plane.normal)) / denominator
                if t < 0.0:
                    return Unresolvable("the plane is behind the ray's origin; the ray never reaches it")
                return Resolvable(Point3Value(coord=ray.point_at(t), frame=WORLD_FRAME))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
