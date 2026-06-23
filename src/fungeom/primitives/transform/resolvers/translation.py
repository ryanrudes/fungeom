"""A pure-translation transform built from a (deferred) vector.

The non-trivial transform resolver: its resolvability is inherited from a
``Vec3``, so you can build a transform out of a vector that is itself
still being computed.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class TranslationTransform(Transform):
    """A pure translation by ``vector`` — resolvable iff the vector is."""

    vector: Vec3

    def _decide(self) -> RigidTransformDecision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(RigidTransform.from_translation(decided.value))
