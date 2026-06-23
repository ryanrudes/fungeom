"""The cross product of two directions — partial when they are parallel."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value


@dataclass(frozen=True, eq=False)
class CrossDirection3(Direction3):
    """The unit direction perpendicular to both ``a`` and ``b``.

    Unresolvable when the two directions are parallel or antiparallel — their
    cross product is the zero vector, which has no direction.
    """

    a: Direction3
    b: Direction3

    def _decide(self) -> Direction3Decision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                perp = np.cross(a.vector, b.vector)
                if float(np.linalg.norm(perp)) == 0.0:
                    return Unresolvable("cross product of parallel directions is undefined")
                return Resolvable(Direction3Value(vector=perp))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
