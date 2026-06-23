"""Generic numpy helpers in core.arrays."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom.core.arrays import freeze


def test_freeze_makes_an_array_read_only() -> None:
    arr = np.array([1.0, 2.0, 3.0])
    freeze(arr)
    with pytest.raises(ValueError):
        arr[0] = 9.0
