"""A plane with the opposite normal."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane


@dataclass(frozen=True, eq=False)
class PlaneFlipped(Plane):
    """``plane`` with its normal negated — total."""

    plane: Plane

    def _decide(self) -> PlaneDecision:
        match self.plane.decide():
            case Resolvable(value):
                return Resolvable(value.flipped())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
