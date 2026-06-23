"""The dot product of two directions — the cosine of the angle between them."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Direction3Dot(Scalar):
    """``a · b`` ∈ ``[-1, 1]`` — the cosine of the angle between two unit directions.

    Total (resolvable iff both directions are): unit vectors always have a
    well-defined dot product.
    """

    a: Direction3
    b: Direction3

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(float(np.dot(a.vector, b.vector)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
