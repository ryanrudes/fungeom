"""A resolver for an already-known transform, plus coercion."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform


@dataclass(frozen=True, eq=False)
class LiteralTransform(Transform):
    """A transform that is already known — always resolvable."""

    value: RigidTransform

    def _decide(self) -> RigidTransformDecision:
        return Resolvable(self.value)


def as_transform_resolver(value: RigidTransform | Transform) -> Transform:
    """Lift a bare :class:`RigidTransform` into a literal resolver; pass resolvers through."""
    if isinstance(value, Transform):
        return value
    return LiteralTransform(value=value)
