"""Some unit direction perpendicular to a given one — total."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value


@dataclass(frozen=True, eq=False)
class AnyPerpendicular(Direction3):
    """An arbitrary unit direction perpendicular to ``direction``.

    Total: a unit vector always has perpendiculars. The choice is deterministic but
    arbitrary — crossing with the coordinate axis least aligned with ``direction`` (so
    the cross is never near-zero). For the don't-care in-plane axis of a surface frame.
    """

    direction: Direction3

    def _decide(self) -> Direction3Decision:
        match self.direction.decide():
            case Resolvable(value):
                helper = np.zeros(3)
                helper[int(np.argmin(np.abs(value.vector)))] = 1.0
                return Resolvable(Direction3Value(vector=np.cross(value.vector, helper)))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
