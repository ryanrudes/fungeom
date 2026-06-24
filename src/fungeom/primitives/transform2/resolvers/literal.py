"""A resolver for an already-known 2D transform."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.transform2.value import RigidTransform2


@dataclass(frozen=True, eq=False)
class LiteralTransform2(Transform2):
    """A transform that is already known — always resolvable."""

    value: RigidTransform2

    def _decide(self) -> RigidTransform2Decision:
        return Resolvable(self.value)
