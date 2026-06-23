"""The transform *value*: a rigid transform (rotation + translation) in 3D.

A :class:`RigidTransform` is an element of SE(3) stored as a 4x4 homogeneous
matrix. It is the glue between coordinate frames: a frame knows the transform
that maps its own local coordinates into its parent's, and chaining those
transforms is how locally-expressed geometry becomes world-anchored.

A value-only primitive for now — it has its value (and the matrix aliases it
needs) but no resolvers yet; a transform is just numbers, so its eventual
resolvers would be trivially always-resolvable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom.core.arrays import freeze
from fungeom.primitives.vec3.value import Float3, as_vec3

type Mat3 = np.ndarray[tuple[Literal[3], Literal[3]], np.dtype[np.float64]]
"""A 3x3 matrix (e.g. a rotation)."""

type Mat4 = np.ndarray[tuple[Literal[4], Literal[4]], np.dtype[np.float64]]
"""A 4x4 homogeneous transform matrix."""


@dataclass(frozen=True, eq=False)
class RigidTransform:
    """A rigid (rotation + translation) transform, stored as a 4x4 matrix.

    Equality is intentionally identity-based (``eq=False``); use
    :meth:`approx_equal` for numeric comparison, since exact float equality of
    transforms is rarely what you want.
    """

    matrix: Mat4
    """Homogeneous 4x4 matrix mapping local coordinates to the parent frame."""

    def __post_init__(self) -> None:
        if self.matrix.shape != (4, 4):
            raise ValueError(f"Transform matrix must be 4x4, got {self.matrix.shape}.")
        # Own a private copy and freeze *that*, so constructing a transform never
        # mutates (the writeability of) the caller's array.
        matrix = np.array(self.matrix, dtype=np.float64)
        freeze(matrix)
        object.__setattr__(self, "matrix", matrix)

    # --- Constructors --------------------------------------------------------

    @classmethod
    def identity(cls) -> RigidTransform:
        """The identity transform (no rotation, no translation)."""
        return cls(np.eye(4, dtype=np.float64))  # type: ignore[arg-type]

    @classmethod
    def from_translation(cls, translation: Float3) -> RigidTransform:
        """A pure translation."""
        m = np.eye(4, dtype=np.float64)
        m[:3, 3] = as_vec3(translation)
        return cls(m)  # type: ignore[arg-type]

    @classmethod
    def from_rotation(cls, rotation: Rotation, translation: Float3 | None = None) -> RigidTransform:
        """A rotation (a scipy :class:`Rotation`) with an optional translation."""
        m = np.eye(4, dtype=np.float64)
        m[:3, :3] = rotation.as_matrix()
        if translation is not None:
            m[:3, 3] = as_vec3(translation)
        return cls(m)  # type: ignore[arg-type]

    @classmethod
    def from_matrix(cls, matrix: Mat4) -> RigidTransform:
        """Wrap an existing 4x4 matrix (copied into a fresh array)."""
        return cls(np.asarray(matrix, dtype=np.float64).copy())

    # --- Accessors -----------------------------------------------------------

    @property
    def rotation(self) -> Mat3:
        """The 3x3 rotation block."""
        return self.matrix[:3, :3].copy()

    @property
    def translation(self) -> Float3:
        """The translation component."""
        return self.matrix[:3, 3].copy()

    # --- Algebra -------------------------------------------------------------

    def inverse(self) -> RigidTransform:
        """The inverse transform (parent -> local)."""
        r = self.matrix[:3, :3]
        t = self.matrix[:3, 3]
        inv = np.eye(4, dtype=np.float64)
        inv[:3, :3] = r.T
        inv[:3, 3] = -r.T @ t
        return RigidTransform(inv)  # type: ignore[arg-type]

    def compose(self, other: RigidTransform) -> RigidTransform:
        """Return ``self ∘ other`` — apply ``other`` first, then ``self``."""
        return RigidTransform(self.matrix @ other.matrix)

    def __matmul__(self, other: RigidTransform) -> RigidTransform:
        return self.compose(other)

    def apply_point(self, point: Float3) -> Float3:
        """Transform a *position*: rotated and translated."""
        p = as_vec3(point)
        return self.matrix[:3, :3] @ p + self.matrix[:3, 3]

    def apply_vector(self, vector: Float3) -> Float3:
        """Transform a *direction*: rotated only, not translated."""
        return self.matrix[:3, :3] @ as_vec3(vector)

    def approx_equal(self, other: RigidTransform, atol: float = 1e-9) -> bool:
        """Numeric comparison of two transforms within ``atol``."""
        return bool(np.allclose(self.matrix, other.matrix, atol=atol))

    def __repr__(self) -> str:
        tx, ty, tz = self.translation
        parts = [f"translation=[{tx:g}, {ty:g}, {tz:g}]"]
        euler = Rotation.from_matrix(self.matrix[:3, :3]).as_euler("xyz", degrees=True)
        if not np.allclose(euler, 0.0, atol=1e-9):
            ex, ey, ez = euler
            parts.append(f"rotation_xyz°=[{ex:g}, {ey:g}, {ez:g}]")
        return f"RigidTransform({', '.join(parts)})"
