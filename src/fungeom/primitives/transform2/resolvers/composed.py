"""The composition of two 2D transforms."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class ComposedTransform2(Transform2):
    """``a ∘ b`` — apply ``b`` first, then ``a``. Resolvable iff both are."""

    a: Transform2
    b: Transform2

    def _decide(self) -> RigidTransform2Decision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a.compose(b))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
