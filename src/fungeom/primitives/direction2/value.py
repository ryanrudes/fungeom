"""The direction2 *value*: a unit 2D vector, enforced by construction.

A :class:`Direction2Value` is the 2D sibling of
:class:`~fungeom.values.Direction3Value` — a planar direction constrained to unit
length. Construction normalizes its input and rejects the zero vector (which has no
direction). In 2D a direction has a unique perpendicular (a quarter turn) and a single
signed angle, so it carries a little more structure than its 3D cousin.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec2.value import Float2, as_vec2


@dataclass(frozen=True, eq=False)
class Direction2Value:
    """A unit-length 2D direction.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for tolerant
    numeric comparison.
    """

    vector: Float2

    def __post_init__(self) -> None:
        vector = as_vec2(self.vector)
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            raise ValueError("a direction cannot be the zero vector")
        vector = vector / norm + 0.0  # the ``+ 0.0`` canonicalizes -0.0 to 0.0
        freeze(vector)
        object.__setattr__(self, "vector", vector)

    @classmethod
    def of(cls, x: float, y: float) -> Direction2Value:
        """Build a direction value from components (normalized; rejects the zero vector)."""
        return cls(vector=as_vec2((x, y)))

    @classmethod
    def from_angle(cls, angle: float) -> Direction2Value:
        """The unit direction at ``angle`` radians from +x (counter-clockwise)."""
        return cls(vector=as_vec2((np.cos(angle), np.sin(angle))))

    def reversed(self) -> Direction2Value:
        """The opposite direction."""
        return Direction2Value(vector=-self.vector)

    def perpendicular(self) -> Direction2Value:
        """The left perpendicular — a quarter turn counter-clockwise (``(x, y) → (-y, x)``)."""
        x, y = self.vector
        return Direction2Value(vector=as_vec2((-y, x)))

    def angle(self) -> float:
        """This direction's angle (radians) from +x, in ``(-π, π]``."""
        x, y = self.vector
        return float(np.arctan2(y, x))

    def angle_to(self, other: Direction2Value) -> float:
        """The unsigned angle (radians) between this direction and ``other``."""
        dot = float(np.clip(np.dot(self.vector, other.vector), -1.0, 1.0))
        return float(np.arccos(dot))

    def approx_equal(self, other: Direction2Value, atol: float = 1e-9) -> bool:
        """True if both point the same way within ``atol``."""
        return bool(np.allclose(self.vector, other.vector, atol=atol))

    def __repr__(self) -> str:
        x, y = self.vector
        return f"Direction2Value([{x:g}, {y:g}])"
