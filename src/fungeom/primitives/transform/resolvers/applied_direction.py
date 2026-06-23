"""A direction with a rigid transform's rotation applied."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class TransformedDirection3(Direction3):
    """``transform``'s rotation applied to a ``direction`` (stays unit length).

    Resolvable iff both are: rotating a unit direction always yields one.
    """

    transform: Transform
    direction: Direction3

    def _decide(self) -> Direction3Decision:
        match self.transform.decide(), self.direction.decide():
            case Resolvable(t), Resolvable(d):
                return Resolvable(Direction3Value(vector=t.apply_vector(d.vector)))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
