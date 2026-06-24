"""The dot product of two 2D directions — the cosine of the angle between them."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction2.resolvers.base import Direction2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Direction2Dot(Scalar):
    """``a · b`` ∈ ``[-1, 1]`` — the cosine of the angle between two unit directions. Total."""

    a: Direction2
    b: Direction2

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(float(np.dot(a.vector, b.vector)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
