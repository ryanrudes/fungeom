"""Whether a point lies in a region (→ Bool)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.region2.resolvers.base import Region2


@dataclass(frozen=True, eq=False)
class Region2Contains(Bool):
    """Whether ``point`` lies in ``region`` (even-odd rule, boundary included)."""

    region: Region2
    point: Point2

    def _decide(self) -> BoolDecision:
        match self.region.decide(), self.point.decide():
            case (Resolvable(region), Resolvable(point)):
                return Resolvable(region.contains(point.coord))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
