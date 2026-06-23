"""A leaf resolver wrapping a known framed point."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class LocatedPoint3(Point3):
    """A leaf resolver for a literal :class:`Point3Value`.

    Resolvable iff the point's frame is grounded.
    """

    point: Point3Value

    def _decide(self) -> Point3Decision:
        if not self.point.is_grounded:
            return Unresolvable(f"frame {self.point.frame.name!r} is not grounded to the world")
        return Resolvable(self.point.world())
