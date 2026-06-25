"""A point's signed distance to a region (→ Scalar) — the balance-board / ZMP stability margin."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Region2SignedDistance(Scalar):
    """The signed distance from ``point`` to ``region`` — positive inside, negative outside.

    The stability margin of a support polygon: how far the centre of pressure is from the
    edge, with sign telling inside from outside. Unresolvable for an empty region (no
    boundary to measure against).
    """

    region: Region2
    point: Point2

    def _decide(self) -> ScalarDecision:
        match self.region.decide(), self.point.decide():
            case (Resolvable(region), Resolvable(point)):
                if region.is_empty:
                    return Unresolvable("the signed distance to an empty region is undefined")
                return Resolvable(region.signed_distance(point.coord))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
