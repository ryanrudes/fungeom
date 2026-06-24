"""``Vec3Signal`` — a 3-vector that varies over time.

A thin facade over the generic :mod:`~fungeom.primitives.signals.series` core,
identical in shape to ``ScalarSignal`` but for ``Float3`` samples. Its blend is
componentwise linear (a flat space, so total); only value parsing and the rich
:meth:`at` return type differ — the reconstruction/boundary/resample logic is shared.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.scalar import SCALAR_BLEND, ScalarSignal
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_lifted,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    decide_sampled,
)
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.vec3.decidability import Vec3Decision
from fungeom.primitives.vec3.resolvers.base import Vec3
from fungeom.primitives.vec3.value import Float3, as_vec3


class _Vec3Blend:
    """Componentwise linear interpolation of vectors — a flat space, so always total."""

    def between(self, a: Float3, b: Float3, frac: float) -> Resolvability[Float3]:
        return Resolvable(as_vec3(a + frac * (b - a)))


VEC3_BLEND = _Vec3Blend()


class Vec3Signal(Signal[Float3]):
    """A deferred 3-vector-valued function of time.

    Mirror of ``ScalarSignal`` one dimension wider: :meth:`at` returns a ``Vec3``;
    ``resolve()`` yields a ``SampledSeries[Float3]``.
    """

    type Value = SampledSeries[Float3]
    """The resolved value type — a ``SampledSeries`` of 3-vectors."""

    @classmethod
    def sampled(
        cls,
        sampling: Sampling,
        values: Sequence[Sequence[float]],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> Vec3Signal:
        """A signal of ``(N, 3)`` ``values`` over ``sampling``, read ``via`` a kernel.

        Samples spaced more than ``max_gap`` seconds apart are treated as a dropout.
        """
        return _SampledVec3Signal(
            sampling=sampling,
            values=tuple(as_vec3(row) for row in values),
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    @classmethod
    def from_samples(
        cls,
        times: ArrayLike,
        values: Sequence[Sequence[float]],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> Vec3Signal:
        """A signal sampled at explicit ``times`` (sugar over :meth:`sampled`)."""
        return cls.sampled(Sampling.at_times(times), values, via=via, outside=outside, max_gap=max_gap)

    def at(self, instant: Instant | float) -> Vec3:
        """The value of this signal at ``instant`` (Unresolvable outside its domain)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _Vec3SampleAt(signal=self, instant=as_instant_resolver(instant))

    def resample(self, onto: Sampling) -> Vec3Signal:
        """This signal reconstructed onto a new time base (Unresolvable if a target is undefined)."""
        return _ResampledVec3Signal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap) -> Vec3Signal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedVec3Signal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> Vec3Signal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedVec3Signal(source=self, to=window)

    def shift(self, by: Duration | float) -> Vec3Signal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))

    def __add__(self, other: Vec3Signal) -> Vec3Signal:
        """Pointwise sum with ``other``, time-aligned on the union of their samples."""
        return _SumVec3Signal(a=self, b=other)

    def __sub__(self, other: Vec3Signal) -> Vec3Signal:
        """Pointwise difference with ``other``, time-aligned."""
        return _DiffVec3Signal(a=self, b=other)

    def dot(self, other: Vec3Signal) -> ScalarSignal:
        """Pointwise dot product with ``other`` over time (→ ``ScalarSignal``), time-aligned."""
        return _DotScalarSignal(a=self, b=other)


@dataclass(frozen=True, eq=False)
class _SampledVec3Signal(Vec3Signal):
    sampling: Sampling
    values: tuple[Float3, ...]
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_sampled(self.sampling, self.values, self.interpolation, self.boundary, VEC3_BLEND, self.max_gap)


@dataclass(frozen=True, eq=False)
class _ResampledVec3Signal(Vec3Signal):
    source: Vec3Signal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedVec3Signal(Vec3Signal):
    source: Vec3Signal
    by: TimeMap

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedVec3Signal(Vec3Signal):
    source: Vec3Signal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _SumVec3Signal(Vec3Signal):
    a: Vec3Signal
    b: Vec3Signal

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t) + self.b.at(t), VEC3_BLEND)


@dataclass(frozen=True, eq=False)
class _DiffVec3Signal(Vec3Signal):
    a: Vec3Signal
    b: Vec3Signal

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t) - self.b.at(t), VEC3_BLEND)


@dataclass(frozen=True, eq=False)
class _DotScalarSignal(ScalarSignal):
    """The pointwise dot product of two vector signals — a ``ScalarSignal``."""

    a: Vec3Signal
    b: Vec3Signal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t).dot(self.b.at(t)), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _Vec3SampleAt(Vec3):
    signal: Vec3Signal
    instant: Instant

    def _decide(self) -> Vec3Decision:
        return decide_sample(self.signal, self.instant)
