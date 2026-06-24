"""A surface coordinate frame on a plane (→ Transform) — the patch-frame assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import Mat4, RigidTransform


@dataclass(frozen=True, eq=False)
class PlaneFrame(Transform):
    """The canonical right-handed surface frame at ``origin``: ``+z`` = normal, ``+x`` = in-plane ``tangent``.

    The world placement of the local patch frame. Unresolvable when ``tangent`` is
    parallel to the plane normal (there is then no in-plane ``x`` axis).
    """

    plane: Plane
    origin: Point3
    tangent: Direction3

    def _decide(self) -> RigidTransformDecision:
        match self.plane.decide(), self.origin.decide(), self.tangent.decide():
            case (Resolvable(plane), Resolvable(origin), Resolvable(tangent)):
                z = plane.normal
                in_plane = tangent.vector - np.dot(tangent.vector, z) * z
                magnitude = float(np.linalg.norm(in_plane))
                if magnitude == 0.0:
                    return Unresolvable("the tangent is parallel to the plane normal; there is no in-plane x axis")
                x = in_plane / magnitude
                y = np.cross(z, x)
                matrix = np.eye(4)
                matrix[:3, 0] = x
                matrix[:3, 1] = y
                matrix[:3, 2] = z
                matrix[:3, 3] = origin.coord
                return Resolvable(RigidTransform.from_matrix(cast(Mat4, matrix)))
            case (Unresolvable() as bad, _, _):
                return bad
            case (_, Unresolvable() as bad, _):
                return bad
            case (_, _, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
