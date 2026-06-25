"""A disc region, approximated by a regular polygon (a literal constructor)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.value import Region2Value


@dataclass(frozen=True, eq=False)
class DiscRegion2(Region2):
    """A disc of ``radius`` at ``(cx, cy)`` as a counter-clockwise ``segments``-gon.

    Unresolvable if ``radius ≤ 0`` or ``segments < 3`` (no polygon). The disc is *approximated*
    — its area/boundary are the inscribed polygon's, exact on that representation.
    """

    radius: float
    cx: float
    cy: float
    segments: int

    def _decide(self) -> Region2Decision:
        if self.radius <= 0.0:
            return Unresolvable(f"a disc needs a positive radius, got {self.radius}")
        if self.segments < 3:
            return Unresolvable(f"a disc polygon needs at least 3 segments, got {self.segments}")
        angles = np.linspace(0.0, 2.0 * np.pi, self.segments, endpoint=False)
        ring = np.column_stack([self.cx + self.radius * np.cos(angles), self.cy + self.radius * np.sin(angles)])
        return Resolvable(Region2Value(rings=(ring,)))
