"""Interpolation — the V-agnostic kernels, exercised through a trivial blend."""

from __future__ import annotations

import numpy as np

from fungeom import Interpolation
from fungeom.core.resolvability import Resolvability, Resolvable


class _LinearBlend:
    def between(self, a: float, b: float, frac: float) -> Resolvability[float]:
        return Resolvable(a + frac * (b - a))


BLEND = _LinearBlend()
TIMES = np.array([0.0, 1.0, 3.0], dtype=np.float64)
VALUES = (10.0, 20.0, 0.0)


def at(kernel: Interpolation, t: float) -> float:
    return kernel.evaluate(TIMES, VALUES, BLEND, t).unwrap()


def test_linear() -> None:
    assert at(Interpolation.linear, 0.5) == 15.0  # interior, via the blend
    assert at(Interpolation.linear, 2.0) == 10.0  # second segment
    assert at(Interpolation.linear, 1.0) == 20.0  # exact node
    assert at(Interpolation.linear, 0.0) == 10.0  # first
    assert at(Interpolation.linear, 3.0) == 0.0  # last


def test_hold() -> None:
    assert at(Interpolation.hold, 0.0) == 10.0  # first
    assert at(Interpolation.hold, 0.9) == 10.0  # before second
    assert at(Interpolation.hold, 1.0) == 20.0  # at node
    assert at(Interpolation.hold, 2.5) == 20.0  # carries previous


def test_nearest() -> None:
    assert at(Interpolation.nearest, 0.0) == 10.0  # first
    assert at(Interpolation.nearest, 0.4) == 10.0  # closer to 0
    assert at(Interpolation.nearest, 0.6) == 20.0  # closer to 1
    assert at(Interpolation.nearest, 3.0) == 0.0  # last
