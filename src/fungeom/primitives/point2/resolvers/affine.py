"""A weighted (affine) combination of 2D points — generalizes centroid and lerp."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
from fungeom.primitives.vec2.value import as_vec2


@dataclass(frozen=True, eq=False)
class AffineCombination2(Point2):
    """``∑ wᵢ pᵢ / ∑ wᵢ`` — Unresolvable if any input is, if there are no points, or if weights total zero."""

    points: tuple[Point2, ...]
    weights: tuple[Scalar, ...]

    def _decide(self) -> Point2Decision:
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
        return Resolvable(Point2Value(coord=as_vec2(coord), frame=WORLD_FRAME2))


def affine_combination2(
    points: Sequence[Point2],
    weights: Sequence[float | Scalar],
) -> Point2:
    """A weighted combination of ``points`` with the given ``weights``."""
    if len(points) != len(weights):
        raise ValueError("points and weights must have the same length")
    return AffineCombination2(
        points=tuple(points),
        weights=tuple(as_scalar_resolver(w) for w in weights),
    )
