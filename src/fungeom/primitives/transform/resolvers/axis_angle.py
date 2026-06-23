"""A rotation transform from a (deferred) axis and a (deferred) angle."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class AxisAngleTransform(Transform):
    """A rotation of ``angle`` radians about ``axis``.

    Both are deferred, so this is resolvable iff both are — and Unresolvable for
    the zero axis, about which a rotation is undefined.
    """

    axis: Vec3
    angle: Scalar

    def _decide(self) -> RigidTransformDecision:
        match self.axis.decide(), self.angle.decide():
            case Resolvable(axis), Resolvable(angle):
                norm = float(np.linalg.norm(axis))
                if norm == 0.0:
                    return Unresolvable("rotation about the zero axis is undefined")
                rotation = Rotation.from_rotvec((axis / norm) * angle)
                return Resolvable(RigidTransform.from_rotation(rotation))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
