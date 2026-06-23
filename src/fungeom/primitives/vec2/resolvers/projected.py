"""2D vector projection and rejection — partial when projecting onto zero."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Resolvability, Unresolvable
from fungeom.primitives.vec2.value import Float2, as_vec2
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


def _decide_pair(a: Vec2, b: Vec2) -> Resolvability[tuple[Float2, Float2]]:
    match a.decide(), b.decide():
        case Resolvable(va), Resolvable(vb):
            return Resolvable((va, vb))
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class ProjectedVec2(Vec2):
    """``a`` projected onto ``onto`` — Unresolvable when ``onto`` is the zero vector."""

    a: Vec2
    onto: Vec2

    def _decide(self) -> Vec2Decision:
        decided = _decide_pair(self.a, self.onto)
        if isinstance(decided, Unresolvable):
            return decided
        a, onto = decided.value
        denom = float(np.dot(onto, onto))
        if denom == 0.0:
            return Unresolvable("cannot project onto the zero vector")
        return Resolvable(as_vec2(onto * (float(np.dot(a, onto)) / denom)))


@dataclass(frozen=True, eq=False)
class RejectedVec2(Vec2):
    """``a`` minus its projection onto ``onto`` (the component orthogonal to ``onto``)."""

    a: Vec2
    onto: Vec2

    def _decide(self) -> Vec2Decision:
        decided = _decide_pair(self.a, self.onto)
        if isinstance(decided, Unresolvable):
            return decided
        a, onto = decided.value
        denom = float(np.dot(onto, onto))
        if denom == 0.0:
            return Unresolvable("cannot reject from the zero vector")
        return Resolvable(as_vec2(a - onto * (float(np.dot(a, onto)) / denom)))
