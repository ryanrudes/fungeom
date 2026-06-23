"""Smooth interpolation between two rigid transforms.

Spherically interpolates the rotation (via the relative rotation vector, so any
``t`` extrapolates consistently with the other lerps) and linearly interpolates
the translation.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy.spatial.transform import Rotation

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform


@dataclass(frozen=True, eq=False)
class SlerpTransform(Transform):
    """``slerp(a, b, t)`` — resolvable iff both transforms and ``t`` are."""

    a: Transform
    b: Transform
    t: Scalar

    def _decide(self) -> RigidTransformDecision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(a), Resolvable(b), Resolvable(t):
                rot_a = Rotation.from_matrix(a.rotation)
                rot_b = Rotation.from_matrix(b.rotation)
                delta = (rot_a.inv() * rot_b).as_rotvec()
                rotation = rot_a * Rotation.from_rotvec(delta * t)
                translation = a.translation * (1.0 - t) + b.translation * t
                return Resolvable(RigidTransform.from_rotation(rotation, translation))
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
