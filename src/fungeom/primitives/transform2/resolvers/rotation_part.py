"""A 2D transform with its translation dropped — the rotation alone."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.transform2.value import RigidTransform2


@dataclass(frozen=True, eq=False)
class RotationPart2(Transform2):
    """``transform`` with its translation zeroed — total."""

    transform: Transform2

    def _decide(self) -> RigidTransform2Decision:
        match self.transform.decide():
            case Resolvable(transform):
                matrix = np.eye(3, dtype=np.float64)
                matrix[:2, :2] = transform.rotation
                return Resolvable(RigidTransform2.from_matrix(matrix))  # type: ignore[arg-type]
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
