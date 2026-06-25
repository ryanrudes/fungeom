"""``ScalarSignal`` — a scalar that varies over time.

A thin facade over the generic :mod:`~fungeom.primitives.signals.series` core: it
supplies the scalar :class:`~fungeom.primitives.signals.blend.Blend` (plain linear
interpolation, always total), parses its input, and narrows :meth:`at` to a rich
:class:`~fungeom.Scalar`. All reconstruction / boundary / resample *logic* lives in
the shared core; the concrete resolvers below are one-line delegations.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import intersect
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.sampling.value import TimeSeries
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_derivative,
    decide_lifted,
    decide_lifted_n,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    resolved_rows,
    decide_sampled,
    decide_warped,
)
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp

if TYPE_CHECKING:
    from fungeom.primitives.signals.boolean import BoolSignal


class _ScalarBlend:
    """Linear interpolation of plain numbers — a flat space, so always total."""

    def between(self, a: float, b: float, frac: float) -> Resolvability[float]:
        return Resolvable(a + frac * (b - a))


SCALAR_BLEND = _ScalarBlend()


def _lerp_at(times: TimeSeries, values: tuple[float, ...], t: float) -> float:
    """The linear interpolant of ``values`` at ``t`` (``t`` assumed inside a connected span)."""
    i = min(max(int(np.searchsorted(times, t, side="right")) - 1, 0), len(times) - 2)
    t0, t1 = float(times[i]), float(times[i + 1])
    frac = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
    return values[i] + frac * (values[i + 1] - values[i])


def windowed_breakpoints(
    series: SampledSeries[float], window: tuple[IntervalValue, ...]
) -> list[list[tuple[float, float]]]:
    """The ``(t, value)`` breakpoints of the linear interpolant over ``window`` ∩ support, per clipped run.

    Each clipped run lies within one support span (so its samples are connected), with its own
    endpoints plus every interior sample time as breakpoints — exactly the corners of the
    piecewise-linear function, where its extrema and trapezoid edges live. Empty if the window
    misses the support.
    """
    runs: list[list[tuple[float, float]]] = []
    for span in intersect(series.support.intervals, window):
        lo, hi = span.start, span.end
        cuts = sorted({lo, hi, *(float(t) for t in series.times if lo < float(t) < hi)})
        runs.append([(t, _lerp_at(series.times, series.values, t)) for t in cuts])
    return runs


def _as_coverage(window: Interval | Coverage) -> Coverage:
    """A reduction window as a ``Coverage`` (an ``Interval`` becomes a one-span coverage)."""
    return window if isinstance(window, Coverage) else Coverage.of([window])


def decide_windowed(signal: ScalarSignal, window: Coverage) -> Resolvability[list[list[tuple[float, float]]]]:
    """Decide ``signal`` and ``window`` and return the per-run breakpoints — Unresolvable if disjoint."""
    decided_signal, decided_window = signal.decide(), window.decide()
    if isinstance(decided_signal, Unresolvable):
        return decided_signal
    if isinstance(decided_window, Unresolvable):
        return decided_window
    runs = windowed_breakpoints(decided_signal.value, decided_window.value.intervals)
    if not runs:
        return Unresolvable("the window does not overlap the signal's support")
    return Resolvable(runs)


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

    @classmethod
    def constant(cls, value: float, over: Interval) -> ScalarSignal:
        """A signal holding ``value`` over the span ``over`` (→ ``ScalarSignal``)."""
        return _ConstantScalarSignal(value=float(value), span=over)

    def offset(self, amount: float) -> ScalarSignal:
        """This signal shifted up by a constant ``amount`` (→ ``ScalarSignal``)."""
        return self.map(lambda value: value + Scalar.of(amount))

    def scale(self, factor: float) -> ScalarSignal:
        """This signal multiplied by a constant ``factor`` (→ ``ScalarSignal``)."""
        return self.map(lambda value: value * Scalar.of(factor))

    @classmethod
    def lift(cls, sources: Sequence[Signal[Any]], combine: Callable[..., Scalar]) -> ScalarSignal:
        """Build a scalar signal by combining ``sources`` per instant (the general escape hatch).

        ``combine`` receives each source's value-at-``t`` *resolver*, positionally, and returns a
        ``Scalar`` — e.g. ``ScalarSignal.lift([va, vb], lambda a, b: a.dot(b))`` for two
        ``Vec3Signal``s. Aligned on the union of sample instants ∩ intersection of supports; any
        per-instant partiality flows through. The N-ary temporal twin of ``Bundle.map_*``.
        """
        return _LiftedScalarSignal(sources=tuple(sources), combine=combine)

    def map(self, transform: Callable[[Scalar], Scalar]) -> ScalarSignal:
        """Apply ``transform`` to this signal's value at each instant (→ ``ScalarSignal``).

        The unary lift — e.g. ``signal.map(lambda s: s.clamp(0, 1))``; the op's partiality flows.
        """
        return _LiftedScalarSignal(sources=(self,), combine=transform)

    def at(self, instant: Instant | float) -> Scalar:
        """The value of this signal at ``instant`` (Unresolvable outside its domain)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _ScalarSampleAt(signal=self, instant=as_instant_resolver(instant))

    def resample(self, onto: Sampling) -> ScalarSignal:
        """This signal reconstructed onto a new time base (Unresolvable if a target is undefined)."""
        return _ResampledScalarSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> ScalarSignal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedScalarSignal(source=self, by=by)
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

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        """Resample onto ``onto`` and resolve to a raw ``(T,) array`` — the vectorized readback.

        The sanctioned exit into numpy; resolves eagerly (raises ``UnresolvableError`` if a
        target is off the support).
        """
        return resolved_rows(self.resample(onto), lambda value: value)

    def derivative(self) -> ScalarSignal:
        """The finite-difference time derivative (→ ``ScalarSignal``; Unresolvable with < 2 samples).

        Exact central differences on the sample grid (one-sided at span edges; never across a gap).
        """
        return _DerivativeScalarSignal(source=self)

    def min_over(self, window: Interval | Coverage) -> Scalar:
        """The minimum value over ``window`` (→ ``Scalar``; Unresolvable if it misses the support)."""
        return _ReducedScalar(signal=self, window=_as_coverage(window), kind="min")

    def max_over(self, window: Interval | Coverage) -> Scalar:
        """The maximum value over ``window`` (→ ``Scalar``)."""
        return _ReducedScalar(signal=self, window=_as_coverage(window), kind="max")

    def integral_over(self, window: Interval | Coverage) -> Scalar:
        """The time integral ``∫ signal dt`` over ``window`` (→ ``Scalar``; exact trapezoids)."""
        return _ReducedScalar(signal=self, window=_as_coverage(window), kind="integral")

    def mean_over(self, window: Interval | Coverage) -> Scalar:
        """The time-average over ``window`` — ``integral_over / duration`` (→ ``Scalar``).

        Unresolvable if the window misses the support or its defined part has zero duration.
        """
        return _ReducedScalar(signal=self, window=_as_coverage(window), kind="mean")

    def argmin_over(self, window: Interval | Coverage) -> Instant:
        """The instant of the minimum over ``window`` (→ ``Instant``; first if tied)."""
        return _ArgReducedInstant(signal=self, window=_as_coverage(window), want_max=False)

    def argmax_over(self, window: Interval | Coverage) -> Instant:
        """The instant of the maximum over ``window`` (→ ``Instant``; first if tied)."""
        return _ArgReducedInstant(signal=self, window=_as_coverage(window), want_max=True)

    def lt(self, threshold: float) -> BoolSignal:
        """Where this signal is **below** ``threshold`` over time (→ ``BoolSignal``; exact crossings)."""
        from fungeom.primitives.signals.boolean import _ThresholdBoolSignal

        return _ThresholdBoolSignal(source=self, threshold=float(threshold), satisfies=lambda v: v < threshold)

    def le(self, threshold: float) -> BoolSignal:
        """Where this signal is **at or below** ``threshold`` over time (→ ``BoolSignal``)."""
        from fungeom.primitives.signals.boolean import _ThresholdBoolSignal

        return _ThresholdBoolSignal(source=self, threshold=float(threshold), satisfies=lambda v: v <= threshold)

    def gt(self, threshold: float) -> BoolSignal:
        """Where this signal is **above** ``threshold`` over time (→ ``BoolSignal``; exact crossings)."""
        from fungeom.primitives.signals.boolean import _ThresholdBoolSignal

        return _ThresholdBoolSignal(source=self, threshold=float(threshold), satisfies=lambda v: v > threshold)

    def ge(self, threshold: float) -> BoolSignal:
        """Where this signal is **at or above** ``threshold`` over time (→ ``BoolSignal``)."""
        from fungeom.primitives.signals.boolean import _ThresholdBoolSignal

        return _ThresholdBoolSignal(source=self, threshold=float(threshold), satisfies=lambda v: v >= threshold)

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
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
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
class _DerivativeScalarSignal(ScalarSignal):
    source: ScalarSignal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_derivative(self.source, lambda a, b, dt: (b - a) / dt, SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _ConstantScalarSignal(ScalarSignal):
    """A signal holding one constant value over a span."""

    value: float
    span: Interval

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        match self.span.decide():
            case Resolvable(span):
                times = [span.start] if span.start == span.end else [span.start, span.end]
                return decide_sampled(
                    Sampling.at_times(times),
                    (self.value,) * len(times),
                    Interpolation.linear,
                    Boundary.undefined,
                    SCALAR_BLEND,
                    None,
                )
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _LiftedScalarSignal(ScalarSignal):
    """A scalar signal built by combining N sources per instant — the general lift / map."""

    sources: tuple[Signal[Any], ...]
    combine: Callable[..., Scalar]

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted_n(self.sources, lambda t: self.combine(*(s.at(t) for s in self.sources)), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _ReducedScalar(Scalar):
    """A windowed reduction of a scalar signal — min / max / integral / mean (→ ``Scalar``)."""

    signal: ScalarSignal
    window: Coverage
    kind: str

    def _decide(self) -> ScalarDecision:
        decided = decide_windowed(self.signal, self.window)
        if isinstance(decided, Unresolvable):
            return decided
        runs = decided.value
        if self.kind == "min":
            return Resolvable(min(value for run in runs for _, value in run))
        if self.kind == "max":
            return Resolvable(max(value for run in runs for _, value in run))
        integral = sum(0.5 * (v0 + v1) * (t1 - t0) for run in runs for (t0, v0), (t1, v1) in zip(run, run[1:]))
        if self.kind == "integral":
            return Resolvable(integral)
        duration = sum(run[-1][0] - run[0][0] for run in runs)
        if duration == 0.0:
            return Unresolvable("the mean over a zero-duration window is undefined")
        return Resolvable(integral / duration)


@dataclass(frozen=True, eq=False)
class _ArgReducedInstant(Instant):
    """The instant of the windowed minimum / maximum of a scalar signal (→ ``Instant``)."""

    signal: ScalarSignal
    window: Coverage
    want_max: bool

    def _decide(self) -> InstantDecision:
        decided = decide_windowed(self.signal, self.window)
        if isinstance(decided, Unresolvable):
            return decided
        best_t, best_v = decided.value[0][0]
        for run in decided.value:
            for t, v in run:
                if (v > best_v) if self.want_max else (v < best_v):
                    best_t, best_v = t, v
        return Resolvable(best_t)


@dataclass(frozen=True, eq=False)
class _ScalarSampleAt(Scalar):
    signal: ScalarSignal
    instant: Instant

    def _decide(self) -> ScalarDecision:
        return decide_sample(self.signal, self.instant)
