"""The translation component of a transform, as a vector."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3


@dataclass(frozen=True, eq=False)
class TranslationPart(Vec3):
    """The translation component of ``transform`` — resolvable iff the transform is."""

    transform: Transform

    def _decide(self) -> Vec3Decision:
        decided = self.transform.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(decided.value.translation)
