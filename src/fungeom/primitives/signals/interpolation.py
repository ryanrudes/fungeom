"""Reconstruction kernels — how a discrete signal is read *between* its samples.

An :class:`Interpolation` turns a discrete sampling into a function of continuous
time. It is an enum-free *strategy object* (pass :data:`Interpolation.linear`,
:data:`Interpolation.hold`, or :data:`Interpolation.nearest`, not a string key),
and — crucially for the generic signal core — it is **value-type agnostic**: it
selects *which* samples and *what* fraction, then defers the actual combination to
the value type's :class:`~fungeom.primitives.blend.Blend`. So one kernel family
serves scalars, vectors, directions, and rotations alike; only the blend differs.

``hold`` and ``nearest`` merely *select* an existing sample, so they are total for
every value type; ``linear`` calls ``blend.between`` and inherits its partiality
(e.g. antipodal directions). Kernels only ever see a time within the sample range
— a signal decides off-domain queries before reaching here.

**Invariant (the reconstruction contract, ``docs/time.md``):** an *exact* sample
(``t == times[i]``) returns ``values[i]`` verbatim — every kernel short-circuits it,
so ``blend.between`` is invoked only *strictly between* samples. A blend may be
value-partial (slerp) or support-changing (a point-cloud blend), and this is what
keeps either from corrupting a value the user asked for *exactly*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from fungeom.core.resolvability import Resolvability, Resolvable
from fungeom.primitives.sampling.value import TimeSeries
from fungeom.primitives.signals.blend import Blend


class Interpolation(ABC):
    """How to read a sampled signal between its samples (a reconstruction kernel)."""

    linear: ClassVar[Interpolation]
    """Piecewise-linear interpolation between adjacent samples (via the blend)."""

    hold: ClassVar[Interpolation]
    """Zero-order hold — the most recent sample at or before the query time."""

    nearest: ClassVar[Interpolation]
    """The value of the nearest sample in time."""

    @abstractmethod
    def evaluate[V](self, times: TimeSeries, values: tuple[V, ...], blend: Blend[V], t: float) -> Resolvability[V]:
        """Reconstruct the value at ``t`` (assumed within ``times[0] .. times[-1]``)."""


@dataclass(frozen=True)
class _Linear(Interpolation):
    def evaluate[V](self, times: TimeSeries, values: tuple[V, ...], blend: Blend[V], t: float) -> Resolvability[V]:
        if t <= times[0]:
            return Resolvable(values[0])
        if t >= times[-1]:
            return Resolvable(values[-1])
        hi = int(np.searchsorted(times, t))
        if times[hi] == t:
            return Resolvable(values[hi])  # an exact sample is that sample, never routed through the blend
        lo = hi - 1
        frac = float((t - times[lo]) / (times[hi] - times[lo]))
        return blend.between(values[lo], values[hi], frac)


@dataclass(frozen=True)
class _Hold(Interpolation):
    def evaluate[V](self, times: TimeSeries, values: tuple[V, ...], blend: Blend[V], t: float) -> Resolvability[V]:
        if t <= times[0]:
            return Resolvable(values[0])
        idx = int(np.searchsorted(times, t, side="right")) - 1
        return Resolvable(values[idx])


@dataclass(frozen=True)
class _Nearest(Interpolation):
    def evaluate[V](self, times: TimeSeries, values: tuple[V, ...], blend: Blend[V], t: float) -> Resolvability[V]:
        if t <= times[0]:
            return Resolvable(values[0])
        if t >= times[-1]:
            return Resolvable(values[-1])
        hi = int(np.searchsorted(times, t))
        lo = hi - 1
        nearer_hi = (t - times[lo]) > (times[hi] - t)
        return Resolvable(values[hi] if nearer_hi else values[lo])


Interpolation.linear = _Linear()
Interpolation.hold = _Hold()
Interpolation.nearest = _Nearest()
