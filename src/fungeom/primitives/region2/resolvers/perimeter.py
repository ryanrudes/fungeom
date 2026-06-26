"""A region's boundary length (→ Scalar)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


@dataclass(frozen=True, eq=False)
class Region2Perimeter(Scalar):
    """The total boundary length of ``region`` (outer rings + holes); ``0`` for the empty region. Total."""

    region: Region2

    def _decide(self) -> ScalarDecision:
        match self.region.decide():
            case Resolvable(region):
                return Resolvable(region.perimeter())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
