"""A line through two points — partial when they coincide."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.line.decidability import LineDecision
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.line.value import LineValue
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class LineThroughPoints(Line):
    """The line through ``a`` and ``b``, directed ``a → b`` (Unresolvable if coincident)."""

    a: Point3
    b: Point3

    def _decide(self) -> LineDecision:
        decided = gather((self.a.decide(), self.b.decide()))
        if isinstance(decided, Unresolvable):
            return decided
        pa, pb = (point.coord for point in decided.value)
        direction = pb - pa
        if float(np.linalg.norm(direction)) == 0.0:
            return Unresolvable("two coincident points do not define a line")
        return Resolvable(LineValue(point=pa, direction=direction))
