"""A line's direction oriented to agree with an ordered run of points (→ Direction3).

The line-fit tangent's *orientation*: a least-squares (or constructed) line is a locus
with no inherent forward sense, but a known ordering of points along it picks one. The
points are projected to their line parameters; they must be strictly monotone for the
ordering to be coherent. Increasing parameters keep the line's direction, decreasing
ones reverse it; a tie or a fold-back is ``Unresolvable``.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class LineDirectionAlong(Direction3):
    """``line``'s direction, flipped if needed so ``points`` run forward along it."""

    line: Line
    points: tuple[Point3, ...]

    def _decide(self) -> Direction3Decision:
        if len(self.points) < 2:
            return Unresolvable("orienting a line needs at least two ordered points")
        match self.line.decide():
            case Resolvable(line):
                decided = gather(tuple(point.decide() for point in self.points))
                if isinstance(decided, Unresolvable):
                    return decided
                parameters = [line.parameter(point.coord) for point in decided.value]
                steps = [later - earlier for earlier, later in zip(parameters, parameters[1:])]
                if all(step > 0.0 for step in steps):
                    return Resolvable(Direction3Value(vector=line.direction))
                if all(step < 0.0 for step in steps):
                    return Resolvable(Direction3Value(vector=-line.direction))
                return Unresolvable("the points are not in coherent monotone order along the line")
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
