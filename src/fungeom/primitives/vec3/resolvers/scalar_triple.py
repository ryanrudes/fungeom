"""The scalar triple product of three vectors (G12) — a signed volume."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class Vec3ScalarTriple(Scalar):
    """``a · (b × c)`` — the signed volume of the parallelepiped they span (a winding sign). Total."""

    a: Vec3
    b: Vec3
    c: Vec3

    def _decide(self) -> ScalarDecision:
        match self.a.decide(), self.b.decide(), self.c.decide():
            case (Resolvable(a), Resolvable(b), Resolvable(c)):
                return Resolvable(float(np.dot(a, np.cross(b, c))))
            case (Unresolvable() as bad, _, _):
                return bad
            case (_, Unresolvable() as bad, _):
                return bad
            case (_, _, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
