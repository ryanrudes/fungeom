"""Generic numpy helpers shared across primitives.

These have no geometric meaning of their own — they are the small,
primitive-agnostic array utilities that the value types lean on. Keeping them in
``core`` lets every primitive (vectors, transforms, points) depend on them
without any of them depending on each other.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

type ArrayLike = npt.ArrayLike
"""Anything coercible into an array: a numpy array, a list, a tuple of numbers."""


def freeze(arr: npt.NDArray[Any]) -> None:
    """Mark a numpy array read-only, in place.

    Used by the frozen value dataclasses so that an immutable value object cannot
    have its backing buffer mutated out from under it.
    """
    arr.setflags(write=False)


def dot2(a: npt.NDArray[Any], b: npt.NDArray[Any]) -> npt.NDArray[Any]:
    """The 2-D dot product, summed in a **fixed** order — ``a₀b₀ + a₁b₁``.

    See :func:`dot3` for why this exists rather than ``np.dot``.
    """
    product: npt.NDArray[Any] = a[..., 0] * b[..., 0] + a[..., 1] * b[..., 1]
    return product


def dot3(a: npt.NDArray[Any], b: npt.NDArray[Any]) -> npt.NDArray[Any]:
    """The 3-D dot product, summed in a **fixed** order — ``a₀b₀ + a₁b₁ + a₂b₂``.

    **Why not ``np.dot`` / ``@``.** Both hand a small fixed-size product to BLAS, which is free to
    associate the sum however its kernel and the host architecture prefer. Three routes into BLAS —
    ``np.dot`` on a pair of 3-vectors, ``matrix @ vector``, and ``block @ matrix.T`` — can therefore
    return three different last bits for the same mathematical quantity, and *which* of them agree
    varies by platform: they coincide on arm64 macOS and diverge on x86-64 Linux. That is exactly
    the kind of difference a library like this must not have, because the whole promise is that a
    graph resolves to a value — not to a value that depends on where it was resolved.

    So the association is **fungeom's own**: one written-out expression, broadcasting over any
    leading axes, used by the per-item path and its batched twin alike. A scalar method and its
    ``_block`` counterpart calling this cannot disagree — not because they were tested and found
    equal on some machine, but because they evaluate the same operations in the same order.
    """
    product: npt.NDArray[Any] = a[..., 0] * b[..., 0] + a[..., 1] * b[..., 1] + a[..., 2] * b[..., 2]
    return product


def norm3(v: npt.NDArray[Any]) -> npt.NDArray[Any]:
    """The Euclidean length of a 3-vector, over a fixed summation order (see :func:`dot3`).

    ``np.linalg.norm`` reaches BLAS for a single vector but reduces pairwise along an axis, so it
    is another spelling whose per-item and batched forms need not agree bit for bit.
    """
    length: npt.NDArray[Any] = np.sqrt(dot3(v, v))
    return length
