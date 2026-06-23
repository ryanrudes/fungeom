"""The inverse of a transform."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class InverseTransform(Transform):
    """``transform⁻¹`` — resolvable iff ``transform`` is (a rigid inverse always exists)."""

    transform: Transform

    def _decide(self) -> RigidTransformDecision:
        decided = self.transform.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(decided.value.inverse())
