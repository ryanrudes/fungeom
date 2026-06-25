"""ScalarSignal — the function-with-a-time-hole and its two partiality layers."""

from __future__ import annotations

from fungeom import (
    Boundary,
    Coverage,
    Instant,
    Interpolation,
    Interval,
    Sampling,
    ScalarSignal,
    TimeMap,
    Unresolvable,
)
from fungeom.values import CoverageValue, IntervalValue, SampledSeries


def test_from_samples_and_at() -> None:
    signal = ScalarSignal.from_samples([0.0, 1.0, 3.0], [10.0, 20.0, 0.0])
    assert signal.at(0.5).resolve() == 15.0  # linear interior (bare seconds)
    assert signal.at(Instant.at(1.0)).resolve() == 20.0  # exact node
    # the sample bridges back into the static scalar algebra
    assert (signal.at(0.5) + signal.at(1.0)).resolve() == 35.0


def test_over_is_the_domain() -> None:
    signal = ScalarSignal.from_samples([2.0, 5.0], [1.0, 4.0])
    assert signal.over().resolve() == IntervalValue(2.0, 5.0)


def test_sampled_with_explicit_sampling_and_kernel() -> None:
    base = Sampling.at_times([0.0, 1.0])
    held = ScalarSignal.sampled(base, [10.0, 20.0], via=Interpolation.hold)
    assert held.at(0.6).resolve() == 10.0  # zero-order hold carries the previous sample


def test_sampling_off_domain_is_unresolvable() -> None:
    signal = ScalarSignal.from_samples([0.0, 1.0], [10.0, 20.0])
    decision = signal.at(5.0).decide()  # the signal resolves fine; the *sample* does not
    assert isinstance(decision, Unresolvable)
    assert "no data at t=5s" in decision.reason
    assert signal.is_resolvable  # ...the signal itself is perfectly well-formed


def test_build_level_partiality() -> None:
    assert not ScalarSignal.from_samples([1.0, 0.0], [1.0, 2.0]).is_resolvable  # bad sampling
    decision = ScalarSignal.from_samples([0.0, 1.0, 2.0], [1.0, 2.0]).decide()  # length mismatch
    assert isinstance(decision, Unresolvable)
    assert "2 values for 3 sample times" in decision.reason


def test_resample() -> None:
    signal = ScalarSignal.from_samples([0.0, 1.0, 2.0, 3.0], [0.0, 10.0, 20.0, 30.0])
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(3.0)), 7)
    resampled = signal.resample(grid).resolve()
    assert resampled.times.tolist() == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    assert list(resampled.values) == [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    # resampling past the source's domain is Unresolvable under the default boundary
    past = signal.resample(Sampling.at_times([2.0, 9.0]))
    decision = past.decide()
    assert isinstance(decision, Unresolvable)
    assert "outside the source" in decision.reason


def test_boundary_hold() -> None:
    signal = ScalarSignal.from_samples([0.0, 1.0], [10.0, 20.0], outside=Boundary.hold)
    assert signal.at(5.0).resolve() == 20.0  # clamps to the last sample
    assert signal.at(-3.0).resolve() == 10.0  # clamps to the first sample


def test_boundary_wrap() -> None:
    # periodic over the span [0, 4]: off-domain queries fold back in (modulo the length)
    signal = ScalarSignal.from_samples([0.0, 1.0, 2.0, 4.0], [0.0, 10.0, 20.0, 0.0], outside=Boundary.wrap)
    assert signal.at(5.0).resolve() == 10.0  # 5 -> 1
    assert signal.at(-3.0).resolve() == 10.0  # -3 -> 1
    # a single-instant signal has nothing to wrap around — it folds to the lone sample
    once = ScalarSignal.from_samples([3.0], [7.0], outside=Boundary.wrap)
    assert once.at(5.0).resolve() == 7.0


def test_reparameterize() -> None:
    sig = ScalarSignal.from_samples([0.0, 1.0, 2.0], [0.0, 10.0, 20.0])
    shifted = sig.reparameterize(TimeMap.shift(5.0))  # +5s latency
    assert shifted.over().resolve() == IntervalValue(5.0, 7.0)
    assert shifted.at(6.0).resolve() == 10.0
    slow = sig.reparameterize(TimeMap.rate(2.0))  # half speed
    assert slow.at(2.0).resolve() == 10.0
    rev = sig.reparameterize(TimeMap.rate(-1.0))  # time reversal flips the samples
    assert rev.over().resolve() == IntervalValue(-2.0, 0.0)
    assert rev.at(-2.0).resolve() == 20.0
    assert rev.at(0.0).resolve() == 0.0
    assert not sig.reparameterize(TimeMap.rate(0.0)).is_resolvable  # zero rate collapses


def test_reparameterize_by_warp() -> None:
    from fungeom import TimeWarp

    sig = ScalarSignal.from_samples([0.0, 1.0, 2.0], [0.0, 10.0, 20.0])
    # A nonlinear warp bends the time base through correspondence knots; samples carry.
    warp = TimeWarp.through([(0.0, 0.0), (1.0, 0.5), (2.0, 2.0)])
    bent = sig.reparameterize(warp)
    assert bent.over().resolve() == IntervalValue(0.0, 2.0)  # endpoints map 0↦0, 2↦2
    assert bent.at(2.0).resolve() == 20.0  # sample at source 2 lands at target 2
    assert bent.at(0.5).resolve() == 10.0  # target 0.5 is where source 1 landed
    # A warp must be defined over the whole signal — it invents no data past its knots.
    short = TimeWarp.through([(0.0, 0.0), (1.0, 1.0)])
    decision = sig.reparameterize(short).decide()
    assert isinstance(decision, Unresolvable)
    assert "not defined over the whole signal" in decision.reason


def test_restrict_and_shift() -> None:
    sig = ScalarSignal.from_samples([0.0, 1.0, 2.0, 3.0], [0.0, 10.0, 20.0, 30.0])
    clipped = sig.restrict(Interval.between(Instant.at(0.5), Instant.at(2.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 2.5)
    assert clipped.at(0.5).resolve() == 5.0  # reconstructed left endpoint
    assert clipped.at(1.0).resolve() == 10.0  # interior sample preserved
    assert clipped.at(2.5).resolve() == 25.0  # reconstructed right endpoint
    assert not clipped.at(2.9).is_resolvable  # now outside the restricted domain
    # a window enclosing the whole domain clips to the domain itself
    assert sig.restrict(Interval.between(Instant.at(-5.0), Instant.at(5.0))).over().resolve() == IntervalValue(0.0, 3.0)
    # a window touching at a single instant yields a one-sample signal
    assert sig.restrict(Interval.point(Instant.at(3.0))).over().resolve() == IntervalValue(3.0, 3.0)
    # shift moves the whole domain
    shifted = sig.shift(5.0)
    assert shifted.over().resolve() == IntervalValue(5.0, 8.0)
    assert shifted.at(6.0).resolve() == 10.0
    # a disjoint window is Unresolvable
    assert not sig.restrict(Interval.between(Instant.at(10.0), Instant.at(20.0))).is_resolvable


def test_value_helpers() -> None:
    signal = ScalarSignal.from_samples([0.0, 1.0], [10.0, 20.0]).resolve()
    assert isinstance(signal, SampledSeries)
    assert signal.domain == (0.0, 1.0)
    assert list(signal.values) == [10.0, 20.0]
    assert repr(signal) == "SampledSeries(2 samples over [0, 1])"


def test_defined_at() -> None:
    sig = ScalarSignal.from_samples([0.0, 1.0, 2.0], [0.0, 10.0, 20.0])
    assert sig.defined_at(1.0).resolve() is True
    assert sig.defined_at(Instant.at(2.0)).resolve() is True  # closed at the end
    assert sig.defined_at(5.0).resolve() is False  # outside the domain


def test_gaps_are_honest() -> None:
    # samples at 0,1 then a jump to 10,11; max_gap=2 marks the dropout between them
    sig = ScalarSignal.from_samples([0.0, 1.0, 10.0, 11.0], [0.0, 10.0, 100.0, 110.0], max_gap=2.0)
    assert sig.support().resolve() == CoverageValue((IntervalValue(0.0, 1.0), IntervalValue(10.0, 11.0)))
    assert sig.over().resolve() == IntervalValue(0.0, 11.0)  # the hull still spans the gap
    assert sig.at(0.5).resolve() == 5.0  # inside the first span, reconstructed normally
    assert sig.defined_at(0.5).resolve() is True
    assert sig.defined_at(5.0).resolve() is False  # in the dropout
    decision = sig.at(5.0).decide()  # honest: it will not interpolate across a real hole
    assert isinstance(decision, Unresolvable)
    assert "gap" in decision.reason
    assert repr(sig.resolve()) == "SampledSeries(4 samples over [0, 11], 1 gap)"
    # max_gap with no actual large jump leaves a single contiguous span
    assert ScalarSignal.from_samples([0.0, 1.0, 2.0], [0, 1, 2], max_gap=5.0).support().resolve() == CoverageValue(
        (IntervalValue(0.0, 2.0),)
    )


def test_lifting_arithmetic() -> None:
    # two signals on *different* sample bases combine on the union of their instants
    a = ScalarSignal.from_samples([0.0, 2.0], [0.0, 20.0])
    b = ScalarSignal.from_samples([0.0, 1.0, 2.0], [0.0, 10.0, 0.0])
    total = a + b
    assert total.resolve().times.tolist() == [0.0, 1.0, 2.0]  # b's breakpoint at t=1 is kept
    assert list(total.resolve().values) == [0.0, 20.0, 20.0]
    assert (a - b).at(0.5).resolve() == 0.0  # 5 - 5
    assert (a * b).at(1.0).resolve() == 100.0  # 10 * 10
    assert (a / ScalarSignal.from_samples([0.0, 2.0], [2.0, 2.0])).at(2.0).resolve() == 10.0  # 20 / 2


def test_lifting_partiality() -> None:
    a = ScalarSignal.from_samples([0.0, 2.0], [0.0, 20.0])
    # a divisor that crosses zero makes the whole quotient Unresolvable (honest)
    assert isinstance((a / ScalarSignal.from_samples([0.0, 2.0], [1.0, 0.0])).decide(), Unresolvable)
    # signals whose supports do not overlap cannot be combined
    decision = (
        ScalarSignal.from_samples([0.0, 1.0], [0.0, 1.0]) + ScalarSignal.from_samples([5.0, 6.0], [0.0, 1.0])
    ).decide()
    assert isinstance(decision, Unresolvable)
    assert "do not overlap" in decision.reason
    # lifting is gap-honest: a gappy operand yields a gappy result
    g = ScalarSignal.from_samples([0.0, 1.0, 10.0, 11.0], [0.0, 10.0, 100.0, 110.0], max_gap=2.0)
    assert (g + g).support().resolve() == CoverageValue((IntervalValue(0.0, 1.0), IntervalValue(10.0, 11.0)))
    assert isinstance((g + g).at(5.0).decide(), Unresolvable)  # in the shared gap


def test_restrict_to_a_gappy_coverage() -> None:
    sig = ScalarSignal.from_samples([0.0, 1.0, 2.0, 3.0, 4.0], [0.0, 10.0, 20.0, 30.0, 40.0])
    keep = Coverage.of(
        [Interval.between(Instant.at(0.0), Instant.at(1.0)), Interval.between(Instant.at(3.0), Instant.at(4.0))]
    )
    clipped = sig.restrict(keep)  # restriction itself introduces a gap
    assert clipped.support().resolve() == CoverageValue((IntervalValue(0.0, 1.0), IntervalValue(3.0, 4.0)))
    assert clipped.at(0.5).resolve() == 5.0
    assert isinstance(clipped.at(2.0).decide(), Unresolvable)  # the carved-out middle


def test_derivative_central_and_one_sided() -> None:
    # f(t) = t² sampled on a uniform grid: central differences are exact for a quadratic
    f = ScalarSignal.from_samples([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 4.0, 9.0])
    d = f.derivative()
    assert d.at(1.0).resolve() == 2.0  # central: (4 − 0) / 2
    assert d.at(2.0).resolve() == 4.0  # central: (9 − 1) / 2
    assert d.at(0.0).resolve() == 1.0  # forward at the left edge
    assert d.at(3.0).resolve() == 5.0  # backward at the right edge
    assert d.over().resolve() == IntervalValue(0.0, 3.0)


def test_derivative_partiality_and_gaps() -> None:
    assert isinstance(ScalarSignal.from_samples([0.0], [5.0]).derivative().decide(), Unresolvable)  # < 2 samples
    # a dropout: the derivative is one-sided at each span edge and Unresolvable inside the gap
    gapped = ScalarSignal.from_samples([0.0, 1.0, 5.0, 6.0], [0.0, 1.0, 5.0, 6.0], max_gap=2.0)
    d = gapped.derivative()
    assert d.at(1.0).resolve() == 1.0  # backward within the first span (not across the gap)
    assert d.at(5.0).resolve() == 1.0  # forward within the second span
    assert isinstance(d.at(3.0).decide(), Unresolvable)  # inside the gap


def test_derivative_isolated_sample_is_unresolvable() -> None:
    # the sample at t=0 is a single-frame island (a gap to the next run) — it has no velocity
    isolated = ScalarSignal.from_samples([0.0, 5.0, 6.0], [0.0, 5.0, 6.0], max_gap=2.0)
    decision = isolated.derivative().decide()
    assert isinstance(decision, Unresolvable)
    assert "isolated sample" in decision.reason


def test_temporal_reductions_over_a_window() -> None:
    # a triangle: 0 → 2 over [0,2], 2 → 0 over [2,4]
    tri = ScalarSignal.from_samples([0.0, 2.0, 4.0], [0.0, 2.0, 0.0])
    full = Interval.between(Instant.at(0.0), Instant.at(4.0))
    assert tri.min_over(full).resolve() == 0.0
    assert tri.max_over(full).resolve() == 2.0
    assert tri.argmin_over(full).resolve() == 0.0  # first if tied
    assert tri.argmax_over(full).resolve() == 2.0
    assert tri.integral_over(full).resolve() == 4.0  # triangle area ½·4·2
    assert tri.mean_over(full).resolve() == 1.0
    # a sub-window with interpolated endpoints: v(1)=1, v(2)=2, v(3)=1
    sub = Interval.between(Instant.at(1.0), Instant.at(3.0))
    assert tri.min_over(sub).resolve() == 1.0
    assert tri.integral_over(sub).resolve() == 3.0  # two trapezoids of 1.5
    assert tri.mean_over(sub).resolve() == 1.5


def test_reductions_over_a_gappy_coverage_window() -> None:
    tri = ScalarSignal.from_samples([0.0, 2.0, 4.0], [0.0, 2.0, 0.0])
    cov = Coverage.of(
        [Interval.between(Instant.at(0.0), Instant.at(1.0)), Interval.between(Instant.at(3.0), Instant.at(4.0))]
    )
    assert tri.integral_over(cov).resolve() == 1.0  # two trapezoids of 0.5 (the [1,3] hump is excluded)
    assert tri.max_over(cov).resolve() == 1.0  # the peak at t=2 is outside the window


def test_reduction_partiality() -> None:
    tri = ScalarSignal.from_samples([0.0, 2.0, 4.0], [0.0, 2.0, 0.0])
    off = Interval.between(Instant.at(10.0), Instant.at(20.0))
    assert isinstance(tri.min_over(off).decide(), Unresolvable)  # window misses the support
    assert isinstance(tri.argmax_over(off).decide(), Unresolvable)
    point = Interval.between(Instant.at(2.0), Instant.at(2.0))
    assert tri.min_over(point).resolve() == 2.0  # a degenerate window still has a value…
    assert isinstance(tri.mean_over(point).decide(), Unresolvable)  # …but no well-defined mean


def test_map_is_the_unary_escape_hatch() -> None:
    s = ScalarSignal.from_samples([0.0, 1.0, 2.0], [-1.0, 2.0, 5.0])
    clamped = s.map(lambda x: x.clamp(0.0, 3.0))
    assert clamped.at(1.0).resolve() == 2.0
    assert clamped.at(2.0).resolve() == 3.0  # clamped to the upper bound
    # the per-instant op's partiality flows: sqrt of the negative sample is Unresolvable
    assert isinstance(s.map(lambda x: x.sqrt()).at(0.0).decide(), Unresolvable)


def test_lift_combines_signals_of_any_type() -> None:
    from fungeom import Vec3Signal

    va = Vec3Signal.from_samples([0.0, 2.0], [[1, 0, 0], [1, 0, 0]])
    vb = Vec3Signal.from_samples([0.0, 2.0], [[0, 1, 0], [1, 0, 0]])
    dot = ScalarSignal.lift([va, vb], lambda a, b: a.dot(b))  # two Vec3Signals → a ScalarSignal
    assert dot.at(0.0).resolve() == 0.0
    assert dot.at(2.0).resolve() == 1.0
    norm = ScalarSignal.lift([va], lambda v: v.norm())  # the single-source (map) case
    assert norm.at(0.0).resolve() == 1.0
    # the result is defined only where all sources overlap
    far = ScalarSignal.from_samples([10.0, 11.0], [1.0, 2.0])
    near = ScalarSignal.from_samples([0.0, 1.0], [1.0, 2.0])
    assert isinstance(ScalarSignal.lift([near, far], lambda a, b: a + b).decide(), Unresolvable)


def test_constant_offset_scale() -> None:
    span = Interval.between(Instant.at(0.0), Instant.at(5.0))
    c = ScalarSignal.constant(3.0, span)
    assert c.at(2.0).resolve() == 3.0
    assert c.over().resolve() == IntervalValue(0.0, 5.0)
    # a degenerate (point) span gives a single-sample constant
    point = Interval.between(Instant.at(3.0), Instant.at(3.0))
    assert ScalarSignal.constant(7.0, point).at(3.0).resolve() == 7.0
    s = ScalarSignal.from_samples([0.0, 2.0], [0.0, 10.0])
    assert s.offset(100.0).at(1.0).resolve() == 105.0
    assert s.scale(2.0).at(1.0).resolve() == 10.0
