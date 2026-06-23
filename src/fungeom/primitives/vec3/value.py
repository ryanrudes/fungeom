"""The vec3 *value*: a frame-free 3D vector.

Three ``float64`` numbers, no coordinate frame. The shaped alias pins the length
into the type so mypy can tell a 3D vector from a 2D one; the constructors are
the single validated entry point for turning loose array-like input into a
canonical vector.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from fungeom.core.arrays import ArrayLike

type Float3 = np.ndarray[tuple[Literal[3]], np.dtype[np.float64]]
"""A 3-dimensional floating-point vector."""


def as_vec3(value: ArrayLike) -> Float3:
    """Coerce ``value`` into a canonical 3D ``float64`` vector.

    Raises ``ValueError`` if the input is not 3-dimensional. The returned array
    is a fresh copy, so callers never alias the caller's buffer.
    """
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.shape != (3,):
        raise ValueError(f"Expected a 3D vector, got shape {np.asarray(value).shape}.")
    return arr.copy()  # type: ignore[return-value]
