"""A plane shifted parallel along its normal."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class PlaneOffset(Plane):
    """``plane`` shifted ``distance`` along its normal — total."""

    plane: Plane
    distance: Scalar

    def _decide(self) -> PlaneDecision:
        match self.plane.decide(), self.distance.decide():
            case Resolvable(plane), Resolvable(distance):
                return Resolvable(plane.offset(distance))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
