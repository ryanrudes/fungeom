"""A region moved by a rigid 2D transform."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.value import Region2Value
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class TransformedRegion2(Region2):
    """``region`` with every boundary vertex moved by the rigid 2D ``transform``.

    Rigid motions preserve orientation and simplicity, so the result is always a valid region.
    """

    region: Region2
    transform: Transform2

    def _decide(self) -> Region2Decision:
        match self.region.decide(), self.transform.decide():
            case (Resolvable(region), Resolvable(transform)):
                rings = tuple(np.array([transform.apply_point(vertex) for vertex in ring]) for ring in region.rings)
                return Resolvable(Region2Value(rings=rings))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
