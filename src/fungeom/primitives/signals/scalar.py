"""``ScalarSignal`` — a scalar that varies over time.

A thin facade over the generic :mod:`~fungeom.primitives.signals.series` core: it
supplies the scalar :class:`~fungeom.primitives.signals.blend.Blend` (plain linear
interpolation, always total), parses its input, and narrows :meth:`at` to a rich
:class:`~fungeom.Scalar`. All reconstruction / boundary / resample *logic* lives in
the shared core; the concrete resolvers below are one-line delegations.
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
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
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


class _ScalarBlend:
    """Linear interpolation of plain numbers — a flat space, so always total."""

    def between(self, a: float, b: float, frac: float) -> Resolvability[float]:
        return Resolvable(a + frac * (b - a))


SCALAR_BLEND = _ScalarBlend()


class ScalarSignal(Signal[float]):
    """A deferred scalar-valued function of time, reconstructed from samples.

    Construct with :meth:`from_samples` or :meth:`sampled`; compose with :meth:`at`
    (→ ``Scalar``), :meth:`over` (→ ``Interval``), and :meth:`resample`.
    ``resolve()`` yields a ``SampledSeries[float]``. Partiality is two-layered: a
    corrupt sampling or count mismatch on *build*, and an off-domain query on
    *sample* (subject to the boundary policy).
    """

    type Value = SampledSeries[float]
    """The resolved value type — a ``SampledSeries`` of plain numbers."""

    @classmethod
    def sampled(
        cls,
        sampling: Sampling,
        values: Sequence[float],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> ScalarSignal:
        """A signal of ``values`` over ``sampling``, read ``via`` a kernel and ``outside`` its ends.

        Samples spaced more than ``max_gap`` seconds apart are treated as a dropout —
        the signal is honestly undefined between them (see :meth:`defined_at`).
        """
        return _SampledScalarSignal(
            sampling=sampling,
            values=tuple(float(v) for v in values),
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    @classmethod
    def from_samples(
        cls,
        times: ArrayLike,
        values: Sequence[float],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> ScalarSignal:
        """A signal sampled at explicit ``times`` (sugar over :meth:`sampled`)."""
        return cls.sampled(Sampling.at_times(times), values, via=via, outside=outside, max_gap=max_gap)

    def at(self, instant: Instant | float) -> Scalar:
        """The value of this signal at ``instant`` (Unresolvable outside its domain)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _ScalarSampleAt(signal=self, instant=as_instant_resolver(instant))

    def resample(self, onto: Sampling) -> ScalarSignal:
        """This signal reconstructed onto a new time base (Unresolvable if a target is undefined)."""
        return _ResampledScalarSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap) -> ScalarSignal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedScalarSignal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> ScalarSignal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint).

        ``to`` may be an ``Interval`` or a (possibly gappy) ``Coverage`` — the latter
        lets a restriction introduce dropouts.
        """
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedScalarSignal(source=self, to=window)

    def shift(self, by: Duration | float) -> ScalarSignal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))

    def __add__(self, other: ScalarSignal) -> ScalarSignal:
        """Pointwise sum with ``other``, time-aligned on the union of their samples."""
        return _SumScalarSignal(a=self, b=other)

    def __sub__(self, other: ScalarSignal) -> ScalarSignal:
        """Pointwise difference with ``other``, time-aligned."""
        return _DiffScalarSignal(a=self, b=other)

    def __mul__(self, other: ScalarSignal) -> ScalarSignal:
        """Pointwise product with ``other``, time-aligned."""
        return _ProductScalarSignal(a=self, b=other)

    def __truediv__(self, other: ScalarSignal) -> ScalarSignal:
        """Pointwise quotient with ``other`` (Unresolvable where the divisor crosses zero)."""
        return _QuotientScalarSignal(a=self, b=other)


@dataclass(frozen=True, eq=False)
class _SampledScalarSignal(ScalarSignal):
    sampling: Sampling
    values: tuple[float, ...]
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_sampled(self.sampling, self.values, self.interpolation, self.boundary, SCALAR_BLEND, self.max_gap)


@dataclass(frozen=True, eq=False)
class _ResampledScalarSignal(ScalarSignal):
    source: ScalarSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedScalarSignal(ScalarSignal):
    source: ScalarSignal
    by: TimeMap

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedScalarSignal(ScalarSignal):
    source: ScalarSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _SumScalarSignal(ScalarSignal):
    a: ScalarSignal
    b: ScalarSignal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t) + self.b.at(t), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _DiffScalarSignal(ScalarSignal):
    a: ScalarSignal
    b: ScalarSignal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t) - self.b.at(t), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _ProductScalarSignal(ScalarSignal):
    a: ScalarSignal
    b: ScalarSignal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t) * self.b.at(t), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _QuotientScalarSignal(ScalarSignal):
    a: ScalarSignal
    b: ScalarSignal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t) / self.b.at(t), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _ScalarSampleAt(Scalar):
    signal: ScalarSignal
    instant: Instant

    def _decide(self) -> ScalarDecision:
        return decide_sample(self.signal, self.instant)
