"""The unit normal of a plane (→ Direction3)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.plane.resolvers.base import Plane


@dataclass(frozen=True, eq=False)
class PlaneNormal(Direction3):
    """The plane's outward unit normal."""

    plane: Plane

    def _decide(self) -> Direction3Decision:
        match self.plane.decide():
            case Resolvable(value):
                return Resolvable(Direction3Value(vector=value.normal))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
