"""Vector projection and rejection — partial when projecting onto zero."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Resolvability, Unresolvable
from fungeom.primitives.vec3.value import Float3, as_vec3
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


def _decide_pair(a: Vec3, b: Vec3) -> Resolvability[tuple[Float3, Float3]]:
    match a.decide(), b.decide():
        case Resolvable(va), Resolvable(vb):
            return Resolvable((va, vb))
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class ProjectedVec3(Vec3):
    """``a`` projected onto ``onto`` — Unresolvable when ``onto`` is the zero vector."""

    a: Vec3
    onto: Vec3

    def _decide(self) -> Vec3Decision:
        decided = _decide_pair(self.a, self.onto)
        if isinstance(decided, Unresolvable):
            return decided
        a, onto = decided.value
        denom = float(np.dot(onto, onto))
        if denom == 0.0:
            return Unresolvable("cannot project onto the zero vector")
        return Resolvable(as_vec3(onto * (float(np.dot(a, onto)) / denom)))


@dataclass(frozen=True, eq=False)
class RejectedVec3(Vec3):
    """``a`` minus its projection onto ``onto`` (the component orthogonal to ``onto``)."""

    a: Vec3
    onto: Vec3

    def _decide(self) -> Vec3Decision:
        decided = _decide_pair(self.a, self.onto)
        if isinstance(decided, Unresolvable):
            return decided
        a, onto = decided.value
        denom = float(np.dot(onto, onto))
        if denom == 0.0:
            return Unresolvable("cannot reject from the zero vector")
        return Resolvable(as_vec3(a - onto * (float(np.dot(a, onto)) / denom)))
