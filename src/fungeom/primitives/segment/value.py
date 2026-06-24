"""The segment *value*: a finite line segment in 3D — two endpoints.

A :class:`SegmentValue` is the bounded member of the line family: it exists only between
``start`` and ``end`` (parameters in ``[0, 1]``), which is exactly a bone between two
joints. Projection clamps to that range. A *degenerate* segment (coincident endpoints)
is a valid value — a single point — but has no direction; that partiality surfaces on
the ``Segment`` facade, not here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class SegmentValue:
    """A finite segment between world-frame endpoints ``start`` and ``end``.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for a tolerant,
    *oriented* comparison (start↔start, end↔end — a reversed segment is a different one).
    """

    start: Float3
    end: Float3

    def __post_init__(self) -> None:
        start = as_vec3(self.start)
        end = as_vec3(self.end)
        freeze(start)
        freeze(end)
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def displacement(self) -> Float3:
        """The vector from ``start`` to ``end``."""
        return as_vec3(self.end - self.start)

    def length(self) -> float:
        """The Euclidean length of the segment."""
        return float(np.linalg.norm(self.end - self.start))

    def midpoint(self) -> Float3:
        """The point halfway along the segment."""
        return as_vec3((self.start + self.end) / 2.0)

    def parameter(self, p: Float3) -> float:
        """The clamped parameter in ``[0, 1]`` of ``p``'s closest point (0 for a degenerate segment)."""
        vector = self.end - self.start
        squared = float(np.dot(vector, vector))
        if squared == 0.0:
            return 0.0
        raw = float(np.dot(as_vec3(p) - self.start, vector) / squared)
        return min(1.0, max(0.0, raw))

    def project(self, p: Float3) -> Float3:
        """The closest point of the segment to ``p`` (clamped to the endpoints)."""
        return as_vec3(self.start + self.parameter(p) * (self.end - self.start))

    def distance_to(self, p: Float3) -> float:
        """The distance from ``p`` to the segment (to the nearer endpoint if past an end)."""
        coord = as_vec3(p)
        return float(np.linalg.norm(coord - self.project(coord)))

    def point_at(self, t: float) -> Float3:
        """The point at parameter ``t`` (caller ensures ``t`` is in ``[0, 1]``)."""
        return as_vec3(self.start + t * (self.end - self.start))

    def approx_equal(self, other: SegmentValue, atol: float = 1e-9) -> bool:
        """True if both segments share endpoints (oriented) within ``atol``."""
        return bool(np.allclose(self.start, other.start, atol=atol) and np.allclose(self.end, other.end, atol=atol))

    def __repr__(self) -> str:
        sx, sy, sz = self.start
        ex, ey, ez = self.end
        return f"SegmentValue(start=[{sx:g}, {sy:g}, {sz:g}], end=[{ex:g}, {ey:g}, {ez:g}])"
