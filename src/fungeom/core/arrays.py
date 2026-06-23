"""Generic numpy helpers shared across primitives.

These have no geometric meaning of their own — they are the small,
primitive-agnostic array utilities that the value types lean on. Keeping them in
``core`` lets every primitive (vectors, transforms, points) depend on them
without any of them depending on each other.
"""

from __future__ import annotations

from typing import Any

import numpy.typing as npt

type ArrayLike = npt.ArrayLike
"""Anything coercible into an array: a numpy array, a list, a tuple of numbers."""


def freeze(arr: npt.NDArray[Any]) -> None:
    """Mark a numpy array read-only, in place.

    Used by the frozen value dataclasses so that an immutable value object cannot
    have its backing buffer mutated out from under it.
    """
    arr.setflags(write=False)
