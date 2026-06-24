"""The generic, value-type-agnostic time-series core shared by every signal.

A :class:`Signal` is a ``Resolver`` whose value is a :class:`SampledSeries` — a time
base plus a tuple of samples of *some* value type ``V`` plus the kernel/boundary/
blend that say how to read it, plus an explicit **support** (a
:class:`~fungeom.primitives.coverage.value.CoverageValue`) saying *where the signal
is genuinely defined*. Everything here is **V-agnostic**: it only ever calls
``blend.between`` (through the interpolation kernel) and otherwise manipulates the
time axis. The per-primitive facades (``ScalarSignal``, ``Vec3Signal``, …) are thin:
they supply a :class:`~fungeom.primitives.blend.Blend`, parse their input, and narrow
the return type of ``at`` to the rich facade — the *logic* lives here, written once.

**Honesty about gaps.** A signal is defined only on its support, not merely on
``[first, last]``. Sampling in an interior *gap* (a dropout — e.g. consecutive
samples spaced beyond a ``max_gap``, or a region carved out by ``restrict``) is
``Unresolvable``: the library refuses to invent data across a hole the way it
refuses every other unanswerable question. The boundary policy applies only past
the *outer* edges of the support, never across an interior gap.

The shared ``decide_*`` helpers are what the facades' tiny concrete resolvers call,
so adding a value type (or an operation) does not re-implement reconstruction, the
boundary policy, the length check, the resample loop, or the support bookkeeping.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from fungeom.core.arrays import freeze
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.coverage.decidability import CoverageDecision
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue, intersect
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.decidability import IntervalDecision
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.sampling.value import TimeSeries, as_times
from fungeom.primitives.signals.blend import Blend
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp


def support_from_times(times: TimeSeries, max_gap: float | None) -> CoverageValue:
    """The support implied by a time base: one span, or one per run of close-enough samples.

    With ``max_gap=None`` the support is the single hull ``[first, last]``. With a
    threshold, any two consecutive samples spaced *more* than ``max_gap`` apart are
    a dropout: the support splits there, so the signal is honestly undefined between
    them. An isolated sample becomes a degenerate ``[t, t]`` span.
    """
    if max_gap is None:
        return CoverageValue((IntervalValue(start=float(times[0]), end=float(times[-1])),))
    spans: list[IntervalValue] = []
    run_start = prev = float(times[0])
    for raw in times[1:]:
        t = float(raw)
        if t - prev > max_gap:
            spans.append(IntervalValue(start=run_start, end=prev))
            run_start = t
        prev = t
    spans.append(IntervalValue(start=run_start, end=prev))
    return CoverageValue(tuple(spans))


@dataclass(frozen=True, eq=False)
class SampledSeries[V]:
    """A sampled function of time: a time base, its samples, how to read them, and its support.

    Generic over the sample type ``V``. It *is* a function of time, but a partial
    one — defined only over its :attr:`support` (subject to the boundary policy at
    the outer edges), and only where the blend succeeds (e.g. not between antipodal
    directions).
    """

    times: TimeSeries
    values: tuple[V, ...]
    interpolation: Interpolation
    boundary: Boundary
    blend: Blend[V]
    support: CoverageValue

    def __post_init__(self) -> None:
        times = as_times(self.times)
        freeze(times)
        object.__setattr__(self, "times", times)

    @property
    def domain(self) -> tuple[float, float]:
        """The closed *hull* of the support — its outer ``[first, last]`` extent."""
        spans = self.support.intervals
        return (spans[0].start, spans[-1].end)

    def in_support(self, t: float) -> bool:
        """Whether ``t`` falls inside some defined span (i.e. not in a gap or off the ends)."""
        return any(span.start <= t <= span.end for span in self.support.intervals)

    def sample(self, t: float) -> Resolvability[V]:
        """The value at ``t``: reconstructed in-support, boundary-mapped past the ends, else Unresolvable.

        A query in an interior gap is ``Unresolvable`` — the boundary policy maps only
        *outside* the support hull, never across a dropout.
        """
        lo, hi = self.domain
        if t < lo or t > hi:
            clamped = self.boundary.outside(t, (lo, hi))
            if clamped is None:
                return Unresolvable(f"no data at t={t:g}s (signal covers {lo:g}–{hi:g}s)")
            t = clamped
        if not self.in_support(t):
            return Unresolvable(f"no data at t={t:g}s (falls in a gap; signal covers {lo:g}–{hi:g}s)")
        return self.interpolation.evaluate(self.times, self.values, self.blend, t)

    def __repr__(self) -> str:
        lo, hi = self.domain
        gaps = len(self.support.intervals) - 1
        suffix = f", {gaps} gap{'s' if gaps != 1 else ''}" if gaps else ""
        return f"SampledSeries({len(self.values)} samples over [{lo:g}, {hi:g}]{suffix})"


class Signal[V](Resolver[SampledSeries[V]]):
    """Generic base for the per-primitive signal facades.

    Beyond being a ``Resolver`` of a :class:`SampledSeries`, it carries the ops whose
    result type is *not* the facade's own primitive — :meth:`over` (→ ``Interval``),
    :meth:`support` (→ ``Coverage``), and :meth:`defined_at` (→ ``Bool``) — written
    once here. The facades add the ops that return their rich type (``at``,
    ``resample``, …) and a :class:`Blend`.
    """

    def over(self) -> Interval:
        """The closed *hull* ``[first, last]`` this signal spans.

        This is the outer extent only; with dropouts the signal is *not* defined
        across the whole hull — use :meth:`support` for the gap-aware answer.
        """
        return SignalDomain(signal=self)

    def support(self) -> Coverage:
        """Where this signal is genuinely defined — a ``Coverage`` (gappy if it has dropouts)."""
        return SignalSupport(signal=self)

    def defined_at(self, instant: Instant | float) -> Bool:
        """Whether this signal has data at ``instant`` (→ ``Bool``): ``support().contains(instant)``.

        Unlike ``over().contains`` this is honest about gaps — it is ``False`` inside a
        dropout, even though the instant lies within the outer hull.
        """
        return self.support().contains(instant)


@dataclass(frozen=True, eq=False)
class SignalDomain[V](Interval):
    """The closed hull ``[first, last]`` a signal spans — V-agnostic, written once.

    This is the *outer extent*; use :meth:`Signal.support` for the gap-aware answer.
    """

    signal: Signal[V]

    def _decide(self) -> IntervalDecision:
        match self.signal.decide():
            case Resolvable(function):
                lo, hi = function.domain
                return Resolvable(IntervalValue(start=lo, end=hi))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class SignalSupport[V](Coverage):
    """The set of spans where a signal is defined — V-agnostic, written once."""

    signal: Signal[V]

    def _decide(self) -> CoverageDecision:
        match self.signal.decide():
            case Resolvable(function):
                return Resolvable(function.support)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


def decide_sampled[V](
    sampling: Sampling,
    values: tuple[V, ...],
    interpolation: Interpolation,
    boundary: Boundary,
    blend: Blend[V],
    max_gap: float | None = None,
) -> Resolvability[SampledSeries[V]]:
    """Build a sampled function — Unresolvable if the sampling is or the counts differ.

    ``max_gap`` (seconds) marks dropouts: consecutive samples spaced beyond it are
    not joined, so the resulting signal is honestly undefined between them.
    """
    match sampling.decide():
        case Resolvable(base):
            if len(values) != base.count:
                return Unresolvable(f"{len(values)} values for {base.count} sample times")
            support = support_from_times(base.times, max_gap)
            return Resolvable(SampledSeries(base.times, values, interpolation, boundary, blend, support))
        case Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_sample[V](signal: Signal[V], instant: Instant) -> Resolvability[V]:
    """Sample ``signal`` at ``instant`` — propagating both layers of partiality."""
    match signal.decide(), instant.decide():
        case Resolvable(function), Resolvable(t):
            return function.sample(t)
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_resampled[V](source: Signal[V], onto: Sampling) -> Resolvability[SampledSeries[V]]:
    """Reconstruct ``source`` onto a new time base — Unresolvable if any target is undefined.

    A target in a gap (or off the ends) cannot be reconstructed, so the whole
    resample is ``Unresolvable``. The result's support is the source's support
    clipped to the new grid's span, so dropouts the grid spanned over survive.
    """
    match source.decide(), onto.decide():
        case Resolvable(function), Resolvable(grid):
            out: list[V] = []
            for t in grid.times:
                point = function.sample(float(t))
                if isinstance(point, Unresolvable):
                    return Unresolvable(f"resample target t={float(t):g}s is outside the source's support")
                out.append(point.value)
            span = IntervalValue(start=float(grid.times[0]), end=float(grid.times[-1]))
            support = CoverageValue(intersect(function.support.intervals, (span,)))
            return Resolvable(
                SampledSeries(
                    grid.times,
                    tuple(out),
                    function.interpolation,
                    function.boundary,
                    function.blend,
                    support,
                )
            )
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_restricted[V](source: Signal[V], to: Coverage) -> Resolvability[SampledSeries[V]]:
    """Narrow a signal's support to its overlap with ``to`` — Unresolvable if they are disjoint.

    Pure masking: the samples and kernel are untouched; only the support shrinks, so
    anything now outside it (including the freshly excluded ends) reads as a gap /
    off-domain. ``to`` is a ``Coverage``, so a restriction can itself introduce gaps.
    """
    match source.decide(), to.decide():
        case Resolvable(function), Resolvable(window):
            kept = intersect(function.support.intervals, window.intervals)
            if not kept:
                return Unresolvable("restriction window does not overlap the signal's support")
            return Resolvable(replace(function, support=CoverageValue(kept)))
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_reparameterized[V](source: Signal[V], by: TimeMap) -> Resolvability[SampledSeries[V]]:
    """Affinely warp a signal's time base — shift / scale / reverse, samples unchanged.

    The support is warped by the same map (so dropouts move with the data).
    Unresolvable when the map has zero rate (it would collapse the whole signal to
    one instant). A negative rate reverses time, so the samples are flipped to keep
    the time base strictly increasing.
    """
    match source.decide(), by.decide():
        case Resolvable(function), Resolvable(timemap):
            if not timemap.is_invertible:
                return Unresolvable("a zero-rate time map collapses the signal")
            times = timemap.offset + timemap.rate * function.times
            values = function.values
            warped: list[IntervalValue] = []
            for span in function.support.intervals:
                lo = timemap.offset + timemap.rate * span.start
                hi = timemap.offset + timemap.rate * span.end
                warped.append(IntervalValue(start=min(lo, hi), end=max(lo, hi)))
            support = CoverageValue(tuple(warped))
            if timemap.rate < 0.0:
                times = times[::-1]
                values = tuple(reversed(values))
            return Resolvable(
                SampledSeries(times, values, function.interpolation, function.boundary, function.blend, support)
            )
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_warped[V](source: Signal[V], by: TimeWarp) -> Resolvability[SampledSeries[V]]:
    """Bend a signal's time base by a monotonic piecewise-linear warp; samples unchanged.

    Each sample time is mapped forward through the warp (strictly increasing, so the
    time base stays ordered) and the support is warped the same way, so dropouts move
    with the data. Unresolvable when the warp is not defined over the whole signal's
    time base — its knots must bracket every sample, because a warp invents no data
    beyond its correspondences (unlike an affine map, which is total).
    """
    match source.decide(), by.decide():
        case Resolvable(function), Resolvable(warp):
            lo, hi = warp.domain
            times = function.times
            if float(times[0]) < lo or float(times[-1]) > hi:
                return Unresolvable("the time warp is not defined over the whole signal's time base")
            warped_times = as_times([warp.apply(float(t)) for t in times])
            warped_support = tuple(
                IntervalValue(start=warp.apply(span.start), end=warp.apply(span.end))
                for span in function.support.intervals
            )
            return Resolvable(
                SampledSeries(
                    warped_times,
                    function.values,
                    function.interpolation,
                    function.boundary,
                    function.blend,
                    CoverageValue(warped_support),
                )
            )
        case Unresolvable() as bad, _:
            return bad
        case _, Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def _union_times_in_support(a: TimeSeries, b: TimeSeries, support: CoverageValue) -> list[float]:
    """The sorted, de-duplicated sample instants of both signals that fall in ``support``."""
    spans = support.intervals
    merged = sorted({float(t) for t in a} | {float(t) for t in b})
    return [t for t in merged if any(span.start <= t <= span.end for span in spans)]


def decide_lifted[U](
    a: Signal[Any],
    b: Signal[Any],
    at_combined: Callable[[float], Resolver[U]],
    blend: Blend[U],
) -> Resolvability[SampledSeries[U]]:
    """Lift a pointwise op over two signals onto their shared, gap-honest time base.

    The two operands are aligned on the *union* of their sample instants, clipped to
    the *intersection* of their supports (so the result is defined only where **both**
    are). ``at_combined(t)`` builds the per-instant combination as an ordinary
    resolver — e.g. ``a.at(t) + b.at(t)`` — so all of the static algebra's partiality
    flows through for free (a ``ScalarSignal`` quotient is ``Unresolvable`` wherever
    the divisor crosses zero). Unresolvable if either operand is, if the supports are
    disjoint, or if any aligned combination is. The result is reconstructed linearly
    between the union instants.
    """
    decided_a, decided_b = a.decide(), b.decide()
    if isinstance(decided_a, Unresolvable):
        return decided_a
    if isinstance(decided_b, Unresolvable):
        return decided_b
    kept = intersect(decided_a.value.support.intervals, decided_b.value.support.intervals)
    if not kept:
        return Unresolvable("the two signals' supports do not overlap")
    support = CoverageValue(kept)
    times = _union_times_in_support(decided_a.value.times, decided_b.value.times, support)
    out: list[U] = []
    for t in times:
        point = at_combined(t).decide()
        if isinstance(point, Unresolvable):
            return point
        out.append(point.value)
    return Resolvable(
        SampledSeries(as_times(times), tuple(out), Interpolation.linear, Boundary.undefined, blend, support)
    )
