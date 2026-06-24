"""Logical negation of a boolean."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool


@dataclass(frozen=True, eq=False)
class NotBool(Bool):
    """``not value`` — resolvable iff ``value`` is."""

    value: Bool

    def _decide(self) -> BoolDecision:
        decided = self.value.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(not decided.value)
