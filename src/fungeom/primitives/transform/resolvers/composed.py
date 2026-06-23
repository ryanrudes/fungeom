"""The composition of two transforms."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class ComposedTransform(Transform):
    """``a ∘ b`` — resolvable iff both transforms are."""

    a: Transform
    b: Transform

    def _decide(self) -> RigidTransformDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a @ b)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
