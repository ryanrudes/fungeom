"""The line where two planes meet — partial when they are parallel."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.line.decidability import LineDecision
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.line.value import LineValue
from fungeom.primitives.plane.resolvers.base import Plane


@dataclass(frozen=True, eq=False)
class PlaneIntersect(Line):
    """The line of intersection of ``first`` and ``second`` (Unresolvable if parallel).

    The line's direction is ``n₁ × n₂`` (zero exactly when the planes are parallel); the
    representative point is the point on the line closest to the origin, solved from the
    two plane equations ``nᵢ · x = nᵢ · pointᵢ``.
    """

    first: Plane
    second: Plane

    def _decide(self) -> LineDecision:
        match self.first.decide(), self.second.decide():
            case Resolvable(a), Resolvable(b):
                direction = np.cross(a.normal, b.normal)
                if float(np.linalg.norm(direction)) == 0.0:
                    return Unresolvable("parallel planes do not meet in a line")
                d1 = float(np.dot(a.normal, a.point))
                d2 = float(np.dot(b.normal, b.point))
                k = float(np.dot(a.normal, b.normal))
                denominator = 1.0 - k * k
                c1 = (d1 - d2 * k) / denominator
                c2 = (d2 - d1 * k) / denominator
                point = c1 * a.normal + c2 * b.normal
                return Resolvable(LineValue(point=point, direction=direction))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
