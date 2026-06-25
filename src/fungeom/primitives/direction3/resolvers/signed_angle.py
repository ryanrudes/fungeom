"""The signed in-plane angle between two directions about an axis (G13)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Direction3SignedAngle(Scalar):
    """The signed angle (radians, right-handed about ``axis``) from ``source`` to ``target``.

    Both directions are projected into the plane perpendicular to ``axis``; the angle between the
    projections is signed by the right-hand rule about ``axis`` (range ``(-π, π]``). Unresolvable
    when either direction is parallel to ``axis`` (its in-plane component vanishes — no angle).
    """

    source: Direction3
    target: Direction3
    axis: Direction3

    def _decide(self) -> ScalarDecision:
        match self.source.decide(), self.target.decide(), self.axis.decide():
            case (Resolvable(s), Resolvable(t), Resolvable(axis)):
                a = axis.vector
                s_perp = s.vector - np.dot(s.vector, a) * a
                t_perp = t.vector - np.dot(t.vector, a) * a
                if float(np.linalg.norm(s_perp)) == 0.0 or float(np.linalg.norm(t_perp)) == 0.0:
                    return Unresolvable("a direction parallel to the axis has no in-plane component to measure")
                angle = np.arctan2(float(np.dot(np.cross(s_perp, t_perp), a)), float(np.dot(s_perp, t_perp)))
                return Resolvable(float(angle))
            case (Unresolvable() as bad, _, _):
                return bad
            case (_, Unresolvable() as bad, _):
                return bad
            case (_, _, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
