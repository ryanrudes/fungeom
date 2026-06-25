"""An axis-aligned rectangular region (a literal constructor)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.value import Region2Value


@dataclass(frozen=True, eq=False)
class RectangleRegion2(Region2):
    """A ``width × height`` rectangle centred at ``(cx, cy)`` — Unresolvable if either extent ≤ 0."""

    width: float
    height: float
    cx: float
    cy: float

    def _decide(self) -> Region2Decision:
        if self.width <= 0.0 or self.height <= 0.0:
            return Unresolvable(f"a rectangle needs positive extents, got {self.width} × {self.height}")
        hw, hh = self.width / 2.0, self.height / 2.0
        ring = np.array(
            [
                [self.cx - hw, self.cy - hh],
                [self.cx + hw, self.cy - hh],
                [self.cx + hw, self.cy + hh],
                [self.cx - hw, self.cy + hh],
            ]
        )
        return Resolvable(Region2Value(rings=(ring,)))
