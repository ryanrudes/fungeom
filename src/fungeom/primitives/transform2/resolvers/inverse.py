"""The inverse of a 2D transform."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class InverseTransform2(Transform2):
    """The inverse of ``transform`` — resolvable iff it is (a rigid transform is invertible)."""

    transform: Transform2

    def _decide(self) -> RigidTransform2Decision:
        match self.transform.decide():
            case Resolvable(transform):
                return Resolvable(transform.inverse())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
