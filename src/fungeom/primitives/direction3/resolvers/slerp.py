"""Spherical interpolation between two directions — partial for antipodes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class SlerpDirection3(Direction3):
    """``slerp(a, b, t)`` along the great circle.

    Unresolvable for antipodal directions (``a == -b``), where no unique great
    circle connects them; resolvable iff both directions and ``t`` are.
    """

    a: Direction3
    b: Direction3
    t: Scalar

    def _decide(self) -> Direction3Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(a), Resolvable(b), Resolvable(t):
                va, vb = a.vector, b.vector
                dot = float(np.clip(np.dot(va, vb), -1.0, 1.0))
                if dot <= -1.0 + 1e-12:
                    return Unresolvable("cannot slerp antipodal directions")
                theta = float(np.arccos(dot))
                if theta < 1e-9:
                    result = va
                else:
                    sin_theta = np.sin(theta)
                    result = (np.sin((1.0 - t) * theta) / sin_theta) * va + (np.sin(t * theta) / sin_theta) * vb
                return Resolvable(Direction3Value(vector=result))
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
