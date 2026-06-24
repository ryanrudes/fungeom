"""A 2D line through two points — partial when they coincide."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.line2.decidability import Line2Decision
from fungeom.primitives.line2.resolvers.base import Line2
from fungeom.primitives.line2.value import Line2Value
from fungeom.primitives.point2.resolvers.base import Point2


@dataclass(frozen=True, eq=False)
class Line2ThroughPoints(Line2):
    """The line through ``a`` and ``b``, directed ``a → b`` (Unresolvable if coincident)."""

    a: Point2
    b: Point2

    def _decide(self) -> Line2Decision:
        decided = gather((self.a.decide(), self.b.decide()))
        if isinstance(decided, Unresolvable):
            return decided
        pa, pb = (point.coord for point in decided.value)
        direction = pb - pa
        if float(np.linalg.norm(direction)) == 0.0:
            return Unresolvable("two coincident points do not define a line")
        return Resolvable(Line2Value(point=pa, direction=direction))
