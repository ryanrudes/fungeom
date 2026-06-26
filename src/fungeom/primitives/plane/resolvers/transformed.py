"""A plane moved rigidly in 3D."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class TransformedPlane(Plane):
    """``plane`` moved by a rigid ``transform`` — the point is moved, the normal rotated. Total."""

    plane: Plane
    transform: Transform

    def _decide(self) -> PlaneDecision:
        match self.plane.decide(), self.transform.decide():
            case Resolvable(plane), Resolvable(transform):
                return Resolvable(plane.transformed_by(transform))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
