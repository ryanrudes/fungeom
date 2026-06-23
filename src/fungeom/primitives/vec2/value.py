"""The vec2 *value*: a frame-free 2D vector.

A value-only primitive for now — it has the canonical type and constructors but
no resolvers yet (2D resolvers wait on 2D coordinate frames). It lives here, with
the other primitives, so its eventual resolvers have an obvious home.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from fungeom.core.arrays import ArrayLike

type Float2 = np.ndarray[tuple[Literal[2]], np.dtype[np.float64]]
"""A 2-dimensional floating-point vector."""


def as_vec2(value: ArrayLike) -> Float2:
    """Coerce ``value`` into a canonical 2D ``float64`` vector."""
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.shape != (2,):
        raise ValueError(f"Expected a 2D vector, got shape {np.asarray(value).shape}.")
    return arr.copy()  # type: ignore[return-value]
