"""The dot and perpendicular-dot (2D cross) products of two 2D vectors, as scalars."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class Vec2Dot(Scalar):
    """``a · b`` — resolvable iff both vectors are."""

    a: Vec2
    b: Vec2

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(float(np.dot(a, b)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class Vec2Cross(Scalar):
    """``a × b = aₓbᵧ − aᵧbₓ`` — the scalar 2D cross product (signed area)."""

    a: Vec2
    b: Vec2

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(float(a[0] * b[1] - a[1] * b[0]))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
