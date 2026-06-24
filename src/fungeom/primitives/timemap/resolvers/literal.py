"""A resolver wrapping an already-known affine time map."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap


@dataclass(frozen=True, eq=False)
class LiteralTimeMap(TimeMap):
    """A time map that is already known — always resolvable."""

    value: AffineTimeMap

    def _decide(self) -> TimeMapDecision:
        return Resolvable(self.value)


def as_timemap_resolver(value: AffineTimeMap | TimeMap) -> TimeMap:
    """Coerce an affine-map *value* into a resolver; pass time-map resolvers through."""
    return value if isinstance(value, TimeMap) else LiteralTimeMap(value=value)
