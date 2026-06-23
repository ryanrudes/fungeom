"""The direction3 *value*: a unit vector, enforced by construction.

A :class:`Direction3Value` is a 3D direction — a vector constrained to unit length.
The value type itself guarantees the invariant: construction normalizes its
input (and rejects the zero vector, which has no direction). So unlike a bare
``Float3``, a ``Direction3Value`` is *always* a unit vector once it exists.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class Direction3Value:
    """A unit-length 3D direction.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for
    tolerant numeric comparison.
    """

    vector: Float3

    def __post_init__(self) -> None:
        vector = as_vec3(self.vector)
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            raise ValueError("a direction cannot be the zero vector")
        vector = vector / norm + 0.0  # the ``+ 0.0`` canonicalizes -0.0 to 0.0
        freeze(vector)
        object.__setattr__(self, "vector", vector)

    @classmethod
    def of(cls, x: float, y: float, z: float) -> Direction3Value:
        """Build a direction value from components (normalized; rejects the zero vector)."""
        return cls(vector=as_vec3((x, y, z)))

    def reversed(self) -> Direction3Value:
        """The opposite direction."""
        return Direction3Value(vector=-self.vector)

    def angle_to(self, other: Direction3Value) -> float:
        """The unsigned angle (radians) between this direction and ``other``."""
        dot = float(np.clip(np.dot(self.vector, other.vector), -1.0, 1.0))
        return float(np.arccos(dot))

    def approx_equal(self, other: Direction3Value, atol: float = 1e-9) -> bool:
        """True if both point the same way within ``atol``."""
        return bool(np.allclose(self.vector, other.vector, atol=atol))

    def __repr__(self) -> str:
        x, y, z = self.vector
        return f"Direction3Value([{x:g}, {y:g}, {z:g}])"
