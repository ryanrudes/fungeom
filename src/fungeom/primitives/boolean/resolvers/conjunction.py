"""Logical conjunction of two booleans."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool


@dataclass(frozen=True, eq=False)
class AndBool(Bool):
    """``a and b`` — resolvable iff both are (strict propagation, not Kleene)."""

    a: Bool
    b: Bool

    def _decide(self) -> BoolDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a and b)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
