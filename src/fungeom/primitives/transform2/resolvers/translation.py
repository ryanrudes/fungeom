"""A pure-translation 2D transform built from a (deferred) vector."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2
from fungeom.primitives.transform2.value import RigidTransform2
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class TranslationTransform2(Transform2):
    """A pure translation by ``vector`` — resolvable iff the vector is."""

    vector: Vec2

    def _decide(self) -> RigidTransform2Decision:
        decided = self.vector.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(RigidTransform2.from_translation(decided.value))
