"""A leaf resolver wrapping a known framed 2D point."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value


@dataclass(frozen=True, eq=False)
class LocatedPoint2(Point2):
    """A leaf resolver for a literal :class:`Point2Value` — resolvable iff its frame is grounded."""

    point: Point2Value

    def _decide(self) -> Point2Decision:
        if not self.point.is_grounded:
            return Unresolvable(f"frame {self.point.frame.name!r} is not grounded to the world")
        return Resolvable(self.point.world())
