"""Smooth interpolation between two 2D rigid transforms (slerp rotation, lerp translation)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.transform2.value import RigidTransform2


@dataclass(frozen=True, eq=False)
class SlerpTransform2(Transform2):
    """Interpolate from ``a`` to ``b`` by ``t`` — the rotation along the shortest arc, the translation linearly.

    Total: a 2D rotation always has a shortest interpolating arc (a half-turn difference
    resolves to ``+π``), and translations interpolate linearly. ``t`` may be deferred.
    """

    a: Transform2
    b: Transform2
    t: Scalar

    def _decide(self) -> RigidTransform2Decision:
        match self.a.decide(), self.b.decide(), self.t.decide():
            case Resolvable(a), Resolvable(b), Resolvable(t):
                delta = float(np.arctan2(np.sin(b.angle() - a.angle()), np.cos(b.angle() - a.angle())))
                angle = a.angle() + t * delta
                translation = (1.0 - t) * a.translation + t * b.translation
                return Resolvable(RigidTransform2.from_angle(angle, translation))
            case Unresolvable() as bad, _, _:
                return bad
            case _, Unresolvable() as bad, _:
                return bad
            case _, _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
