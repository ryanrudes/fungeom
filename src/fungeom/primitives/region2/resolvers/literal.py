"""A literal region from a ready-made value (backs the empty-region constant)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.value import Region2Value


@dataclass(frozen=True, eq=False)
class LiteralRegion2(Region2):
    """A region wrapping an already-built :class:`Region2Value` (total)."""

    value: Region2Value

    def _decide(self) -> Region2Decision:
        return Resolvable(self.value)
