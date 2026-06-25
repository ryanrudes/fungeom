"""A rigid frame from a primary axis, a secondary-axis hint, and an origin (G9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import Mat4, RigidTransform
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class FromAxesTransform(Transform):
    """The right-handed frame at ``origin`` whose ``+x`` is ``primary`` and ``+z`` is ``primary × secondary``.

    ``secondary`` is a *hint*: it is Gram–Schmidt-projected into the plane perpendicular to
    ``primary`` to give ``+y = z × x`` (so the frame is orthonormal even if the two input axes are
    not perfectly perpendicular). The patch frame from a plane tangent + a reference direction.
    Unresolvable when ``primary`` and ``secondary`` are parallel (no third axis exists).
    """

    primary: Direction3
    secondary: Direction3
    origin: Vec3

    def _decide(self) -> RigidTransformDecision:
        match self.primary.decide(), self.secondary.decide(), self.origin.decide():
            case (Resolvable(x), Resolvable(y), Resolvable(o)):
                z = np.cross(x.vector, y.vector)
                z_norm = float(np.linalg.norm(z))
                if z_norm == 0.0:
                    return Unresolvable("from_axes: the primary and secondary axes are parallel; no frame")
                z = z / z_norm
                y_ortho = np.cross(z, x.vector)
                matrix = np.eye(4)
                matrix[:3, 0] = x.vector
                matrix[:3, 1] = y_ortho
                matrix[:3, 2] = z
                matrix[:3, 3] = o
                return Resolvable(RigidTransform.from_matrix(cast(Mat4, matrix)))
            case (Unresolvable() as bad, _, _):
                return bad
            case (_, Unresolvable() as bad, _):
                return bad
            case (_, _, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
