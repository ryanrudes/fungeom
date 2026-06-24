"""A weighted (affine) combination of instants — generalizes centroid and lerp."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable, gather
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver


@dataclass(frozen=True, eq=False)
class AffineInstant(Instant):
    """``∑ wᵢ tᵢ / ∑ wᵢ`` — the centroid (equal weights) and lerp generalized.

    Unresolvable if any input is, if there are no instants, or if the weights
    total zero (the result would be a *duration*, not a point on the timeline).
    """

    instants: tuple[Instant, ...]
    weights: tuple[Scalar, ...]

    def _decide(self) -> InstantDecision:
        if not self.instants:
            return Unresolvable("affine combination of no instants is undefined")
        decided_instants = gather(i.decide() for i in self.instants)
        if isinstance(decided_instants, Unresolvable):
            return decided_instants
        decided_weights = gather(w.decide() for w in self.weights)
        if isinstance(decided_weights, Unresolvable):
            return decided_weights
        total = sum(decided_weights.value)
        if total == 0.0:
            return Unresolvable("affine combination with zero total weight is undefined")
        combined = sum(t * w for t, w in zip(decided_instants.value, decided_weights.value, strict=True))
        return Resolvable(combined / total)


def affine_combination(
    instants: Sequence[Instant],
    weights: Sequence[float | Scalar],
) -> Instant:
    """A weighted combination of ``instants`` with the given ``weights``."""
    if len(instants) != len(weights):
        raise ValueError("instants and weights must have the same length")
    return AffineInstant(
        instants=tuple(instants),
        weights=tuple(as_scalar_resolver(w) for w in weights),
    )
