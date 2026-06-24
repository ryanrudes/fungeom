"""The transform2 *value*: a rigid 2D transform (rotation + translation) in SE(2).

A :class:`RigidTransform2` is the 2D sibling of
:class:`~fungeom.values.RigidTransform` — an element of SE(2) stored as a 3x3
homogeneous matrix (a 2x2 rotation block, a 2-vector translation, and the ``[0, 0, 1]``
bottom row). It is the glue between 2D coordinate frames: a frame knows the transform
mapping its own coordinates into its parent's, and chaining those is how locally
expressed planar geometry becomes world-anchored. In 2D a rotation is a single angle —
there is no axis — so it is always well-defined (unlike SE(3)'s zero-axis case).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec2.value import Float2, as_vec2

type Mat2 = np.ndarray[tuple[Literal[2], Literal[2]], np.dtype[np.float64]]
"""A 2x2 matrix (e.g. a planar rotation)."""

type Mat3 = np.ndarray[tuple[Literal[3], Literal[3]], np.dtype[np.float64]]
"""A 3x3 homogeneous transform matrix (for SE(2))."""


@dataclass(frozen=True, eq=False)
class RigidTransform2:
    """A rigid planar transform (rotation + translation), stored as a 3x3 matrix.

    Equality is intentionally identity-based (``eq=False``); use :meth:`approx_equal`
    for numeric comparison, since exact float equality of transforms is rarely wanted.
    """

    matrix: Mat3
    """Homogeneous 3x3 matrix mapping local 2D coordinates to the parent frame."""

    def __post_init__(self) -> None:
        if self.matrix.shape != (3, 3):
            raise ValueError(f"Transform2 matrix must be 3x3, got {self.matrix.shape}.")
        matrix = np.array(self.matrix, dtype=np.float64)
        freeze(matrix)
        object.__setattr__(self, "matrix", matrix)

    # --- Constructors --------------------------------------------------------

    @classmethod
    def identity(cls) -> RigidTransform2:
        """The identity transform (no rotation, no translation)."""
        return cls(np.eye(3, dtype=np.float64))  # type: ignore[arg-type]

    @classmethod
    def from_translation(cls, translation: Float2) -> RigidTransform2:
        """A pure translation."""
        m = np.eye(3, dtype=np.float64)
        m[:2, 2] = as_vec2(translation)
        return cls(m)  # type: ignore[arg-type]

    @classmethod
    def from_angle(cls, angle: float, translation: Float2 | None = None) -> RigidTransform2:
        """A rotation of ``angle`` radians (counter-clockwise) with an optional translation."""
        cos, sin = np.cos(angle), np.sin(angle)
        m = np.eye(3, dtype=np.float64)
        m[:2, :2] = [[cos, -sin], [sin, cos]]
        if translation is not None:
            m[:2, 2] = as_vec2(translation)
        return cls(m)  # type: ignore[arg-type]

    @classmethod
    def from_matrix(cls, matrix: Mat3) -> RigidTransform2:
        """Wrap an existing 3x3 matrix (copied into a fresh array)."""
        return cls(np.asarray(matrix, dtype=np.float64).copy())

    # --- Accessors -----------------------------------------------------------

    @property
    def rotation(self) -> Mat2:
        """The 2x2 rotation block."""
        return self.matrix[:2, :2].copy()

    @property
    def translation(self) -> Float2:
        """The translation component."""
        return self.matrix[:2, 2].copy()

    def angle(self) -> float:
        """The rotation angle (radians), in ``(-π, π]``."""
        return float(np.arctan2(self.matrix[1, 0], self.matrix[0, 0]))

    # --- Algebra -------------------------------------------------------------

    def inverse(self) -> RigidTransform2:
        """The inverse transform (parent -> local)."""
        r = self.matrix[:2, :2]
        t = self.matrix[:2, 2]
        inv = np.eye(3, dtype=np.float64)
        inv[:2, :2] = r.T
        inv[:2, 2] = -r.T @ t
        return RigidTransform2(inv)  # type: ignore[arg-type]

    def compose(self, other: RigidTransform2) -> RigidTransform2:
        """Return ``self ∘ other`` — apply ``other`` first, then ``self``."""
        return RigidTransform2(self.matrix @ other.matrix)

    def __matmul__(self, other: RigidTransform2) -> RigidTransform2:
        return self.compose(other)

    def apply_point(self, point: Float2) -> Float2:
        """Transform a *position*: rotated and translated."""
        p = as_vec2(point)
        return self.matrix[:2, :2] @ p + self.matrix[:2, 2]

    def apply_vector(self, vector: Float2) -> Float2:
        """Transform a *direction*: rotated only, not translated."""
        return self.matrix[:2, :2] @ as_vec2(vector)

    def approx_equal(self, other: RigidTransform2, atol: float = 1e-9) -> bool:
        """Numeric comparison of two transforms within ``atol``."""
        return bool(np.allclose(self.matrix, other.matrix, atol=atol))

    def __repr__(self) -> str:
        tx, ty = self.translation
        parts = [f"translation=[{tx:g}, {ty:g}]"]
        degrees = float(np.degrees(self.angle()))
        if not np.isclose(degrees, 0.0, atol=1e-9):
            parts.append(f"angle°={degrees:g}")
        return f"RigidTransform2({', '.join(parts)})"
