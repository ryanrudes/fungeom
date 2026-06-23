"""The rotation-only part of a transform (translation zeroed)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform


@dataclass(frozen=True, eq=False)
class RotationPart(Transform):
    """``transform`` with its translation dropped — resolvable iff the transform is."""

    transform: Transform

    def _decide(self) -> RigidTransformDecision:
        decided = self.transform.decide()
        if isinstance(decided, Unresolvable):
            return decided
        matrix = np.eye(4, dtype=np.float64)
        matrix[:3, :3] = decided.value.rotation
        return Resolvable(RigidTransform(matrix))  # type: ignore[arg-type]
