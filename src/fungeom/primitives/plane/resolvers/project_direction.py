"""A direction projected into a plane — partial when it is parallel to the normal."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.plane.resolvers.base import Plane


@dataclass(frozen=True, eq=False)
class PlaneProjectDirection(Direction3):
    """``direction``'s in-plane component, renormalized.

    The Gram-Schmidt of a reference against the plane normal — the in-plane direction a
    tangent-from-reference resolver needs. Unresolvable when ``direction`` is parallel
    to the normal (its in-plane component is the zero vector).
    """

    plane: Plane
    direction: Direction3

    def _decide(self) -> Direction3Decision:
        match self.plane.decide(), self.direction.decide():
            case Resolvable(plane), Resolvable(direction):
                vector = direction.vector
                in_plane = vector - np.dot(vector, plane.normal) * plane.normal
                if float(np.linalg.norm(in_plane)) == 0.0:
                    return Unresolvable("the direction is parallel to the plane normal; it has no in-plane component")
                return Resolvable(Direction3Value(vector=in_plane))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
