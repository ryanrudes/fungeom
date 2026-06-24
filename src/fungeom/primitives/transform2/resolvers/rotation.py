"""A pure-rotation 2D transform from a (deferred) angle — total (no axis in 2D)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.transform2.value import RigidTransform2


@dataclass(frozen=True, eq=False)
class RotationTransform2(Transform2):
    """A rotation by ``angle`` radians — resolvable iff the angle is (a 2D rotation is total)."""

    radians: Scalar

    def _decide(self) -> RigidTransform2Decision:
        decided = self.radians.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(RigidTransform2.from_angle(decided.value))
