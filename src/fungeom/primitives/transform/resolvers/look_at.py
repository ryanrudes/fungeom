"""A viewing frame that looks from an eye toward a target (G10)."""

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
class LookAtTransform(Transform):
    """The right-handed frame at ``eye`` whose ``+z`` looks toward ``target``, ``+y`` roughly ``up``.

    A camera / sensor pose: ``+z`` = forward (the view direction), ``+x`` = right (``up × forward``),
    ``+y`` = ``forward × right``. Unresolvable when ``eye`` coincides with ``target`` (no view
    direction) or ``up`` is parallel to the view direction (no unique right axis).
    """

    eye: Vec3
    target: Vec3
    up: Direction3

    def _decide(self) -> RigidTransformDecision:
        match self.eye.decide(), self.target.decide(), self.up.decide():
            case (Resolvable(eye), Resolvable(target), Resolvable(up)):
                forward = np.asarray(target) - np.asarray(eye)
                forward_norm = float(np.linalg.norm(forward))
                if forward_norm == 0.0:
                    return Unresolvable("look_at: the eye and target coincide; there is no view direction")
                forward = forward / forward_norm
                right = np.cross(up.vector, forward)
                right_norm = float(np.linalg.norm(right))
                if right_norm == 0.0:
                    return Unresolvable("look_at: up is parallel to the view direction; no unique right axis")
                right = right / right_norm
                true_up = np.cross(forward, right)
                matrix = np.eye(4)
                matrix[:3, 0] = right
                matrix[:3, 1] = true_up
                matrix[:3, 2] = forward
                matrix[:3, 3] = np.asarray(eye)
                return Resolvable(RigidTransform.from_matrix(cast(Mat4, matrix)))
            case (Unresolvable() as bad, _, _):
                return bad
            case (_, Unresolvable() as bad, _):
                return bad
            case (_, _, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
