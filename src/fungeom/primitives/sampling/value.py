"""The sampling *value*: a discrete time base.

A :class:`SamplingValue` is a strictly-increasing sequence of master-clock
seconds — the time axis of real, irregularly-sampled data, jitter and all.
Reifying it (rather than burying timestamps inside a signal) is what lets two
signals *share* a time base and lets resampling target *another* signal's
sampling. The honest partiality of real captures — empty or out-of-order
timestamps — lives one layer up, in the resolvers, via :func:`monotonic_reason`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import ArrayLike, freeze

type TimeSeries = np.ndarray[tuple[int], np.dtype[np.float64]]
"""A 1-D array of ``float64`` times (or, reused, of scalar sample values)."""

type FloatArray = np.ndarray[tuple[int, ...], np.dtype[np.float64]]
"""A ``float64`` array of any shape — e.g. ``(N, D)`` sample values."""


def as_times(values: ArrayLike) -> TimeSeries:
    """Coerce array-like input into a fresh 1-D ``float64`` array."""
    return np.asarray(values, dtype=np.float64).reshape(-1).copy()


def monotonic_reason(times: TimeSeries) -> str | None:
    """Why ``times`` is not a valid sampling, or ``None`` if it is.

    A sampling must be non-empty and strictly increasing — duplicate or
    out-of-order timestamps (a corrupt capture) define no function of time.
    """
    if times.shape[0] == 0:
        return "a sampling has no times"
    if bool(np.any(np.diff(times) <= 0.0)):
        return "sampling times are not strictly increasing"
    return None


@dataclass(frozen=True, eq=False)
class SamplingValue:
    """A strictly-increasing discrete time base (master-clock seconds)."""

    times: TimeSeries

    def __post_init__(self) -> None:
        times = as_times(self.times)
        freeze(times)
        object.__setattr__(self, "times", times)

    @property
    def count(self) -> int:
        """The number of sample times."""
        return int(self.times.shape[0])

    def approx_equal(self, other: SamplingValue, atol: float = 1e-9) -> bool:
        """Numeric comparison of two samplings within ``atol``."""
        return self.times.shape == other.times.shape and bool(np.allclose(self.times, other.times, atol=atol))

    def __repr__(self) -> str:
        return f"SamplingValue({self.count} times, span=[{self.times[0]:g}, {self.times[-1]:g}])"
