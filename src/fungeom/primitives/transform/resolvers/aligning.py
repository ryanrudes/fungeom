"""The shortest-arc rotation taking one direction onto another (G8)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform


@dataclass(frozen=True, eq=False)
class AligningTransform(Transform):
    """The rigid rotation (no translation) carrying ``source`` onto ``target`` by the shortest arc.

    Unresolvable when ``source`` and ``target`` are antipodal — opposed directions have no
    *unique* shortest-arc rotation (any half-turn about a perpendicular axis works).
    """

    source: Direction3
    target: Direction3

    def _decide(self) -> RigidTransformDecision:
        match self.source.decide(), self.target.decide():
            case (Resolvable(a), Resolvable(b)):
                axis = np.cross(a.vector, b.vector)
                axis_norm = float(np.linalg.norm(axis))
                cosine = float(np.clip(np.dot(a.vector, b.vector), -1.0, 1.0))
                if axis_norm == 0.0:
                    if cosine > 0.0:
                        return Resolvable(RigidTransform.identity())  # already aligned
                    return Unresolvable("no unique shortest-arc rotation between antipodal directions")
                angle = float(np.arctan2(axis_norm, cosine))
                return Resolvable(RigidTransform.from_rotation(Rotation.from_rotvec(axis / axis_norm * angle)))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
