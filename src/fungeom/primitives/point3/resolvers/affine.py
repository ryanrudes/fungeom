"""A weighted (affine) combination of points — generalizes centroid and lerp."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.frame import WORLD_FRAME
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
from fungeom.primitives.vec3.value import as_vec3


@dataclass(frozen=True, eq=False)
class AffineCombination3(Point3):
    """``∑ wᵢ pᵢ / ∑ wᵢ`` — the centroid (equal weights) and lerp generalized.

    Unresolvable if any input is, if there are no points, or if the weights total
    zero (the result would be a direction, not a point).
    """

    points: tuple[Point3, ...]
    weights: tuple[Scalar, ...]

    def _decide(self) -> Point3Decision:
        if not self.points:
            return Unresolvable("affine combination of no points is undefined")
        decided_points = gather(p.decide() for p in self.points)
        if isinstance(decided_points, Unresolvable):
            return decided_points
        decided_weights = gather(w.decide() for w in self.weights)
        if isinstance(decided_weights, Unresolvable):
            return decided_weights
        if float(np.sum(decided_weights.value)) == 0.0:
            return Unresolvable("affine combination with zero total weight is undefined")
        coord = np.average(
            [p.coord for p in decided_points.value],
            axis=0,
            weights=decided_weights.value,
        )
        return Resolvable(Point3Value(coord=as_vec3(coord), frame=WORLD_FRAME))


def affine_combination(
    points: Sequence[Point3],
    weights: Sequence[float | Scalar],
) -> Point3:
    """A weighted combination of ``points`` with the given ``weights``."""
    if len(points) != len(weights):
        raise ValueError("points and weights must have the same length")
    return AffineCombination3(
        points=tuple(points),
        weights=tuple(as_scalar_resolver(w) for w in weights),
    )
