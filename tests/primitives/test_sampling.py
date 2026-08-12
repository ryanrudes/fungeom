"""Sampling — discrete time bases and the corrupt-capture partialities."""

from __future__ import annotations

import pytest

from fungeom import Instant, Interval, Sampling, Scalar, Unresolvable
from fungeom.values import IntervalValue, SamplingValue


def test_at_times() -> None:
    base = Sampling.at_times([0.0, 0.5, 1.5, 3.0]).resolve()
    assert base.count == 4
    assert base.times.tolist() == [0.0, 0.5, 1.5, 3.0]


def test_uniform() -> None:
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5).resolve()
    assert grid.times.tolist() == [0.0, 0.5, 1.0, 1.5, 2.0]
    assert Sampling.uniform(Interval.point(Instant.at(4.0)), 1).resolve().times.tolist() == [4.0]


def test_at_rate() -> None:
    grid = Sampling.at_rate(2.0, 5).resolve()
    assert grid.times.tolist() == [0.0, 0.5, 1.0, 1.5, 2.0]
    # the same grid `uniform` describes, without the caller writing `count - 1`
    span = Interval.between(Instant.at(0.0), Instant.at(2.0))
    assert grid.approx_equal(Sampling.uniform(span, 5).resolve())
    # a rate and a start may both be deferred, and a single sample is a valid base
    paced = Sampling.at_rate(Scalar.of(4.0), 3, start=Instant.at(1.0)).resolve()
    assert paced.times.tolist() == [1.0, 1.25, 1.5]
    assert Sampling.at_rate(60.0, 1, start=9.0).resolve().times.tolist() == [9.0]
    # 60 fps over 281 frame boundaries — the motion-capture case this exists for
    assert Sampling.at_rate(60.0, 281).rate().resolve() == pytest.approx(60.0)


def test_span_count_rate() -> None:
    base = Sampling.at_times([0.0, 0.5, 1.0, 1.5, 2.0])
    assert base.span().resolve() == IntervalValue(0.0, 2.0)
    assert base.count().resolve() == 5.0
    assert base.rate().resolve() == 2.0  # 4 intervals over 2s -> 2 Hz
    # a single-sample base still has a (degenerate) span and a count
    single = Sampling.at_times([3.0])
    assert single.span().resolve() == IntervalValue(3.0, 3.0)
    assert single.count().resolve() == 1.0


def test_partiality() -> None:
    assert not Sampling.at_times([]).is_resolvable  # empty
    assert not Sampling.at_times([3.0]).rate().is_resolvable  # one sample defines no rate
    assert not Sampling.at_times([1.0, 1.0]).is_resolvable  # duplicate
    decision = Sampling.at_times([0.0, 2.0, 1.0]).decide()  # out of order
    assert isinstance(decision, Unresolvable)
    assert "strictly increasing" in decision.reason
    assert not Sampling.uniform(Interval.point(Instant.at(0.0)), 4).is_resolvable  # degenerate grid
    assert not Sampling.uniform(Interval.between(Instant.at(0), Instant.at(1)), 0).is_resolvable
    assert not Sampling.at_rate(60.0, 0).is_resolvable  # no samples is no time base
    for rate in (0.0, -60.0, float("nan")):  # none of these define a spacing
        stopped = Sampling.at_rate(rate, 4).decide()
        assert isinstance(stopped, Unresolvable)
        assert "rate must be positive" in stopped.reason
    crowded = Sampling.at_rate(float("inf"), 4).decide()  # spacing underflows to nothing
    assert isinstance(crowded, Unresolvable)
    assert "strictly increasing" in crowded.reason


def test_value_helpers() -> None:
    base = Sampling.at_times([0.0, 1.0]).resolve()
    assert base.approx_equal(SamplingValue(times=base.times))
    assert not base.approx_equal(Sampling.at_times([0.0, 1.0, 2.0]).resolve())
    assert repr(base) == "SamplingValue(2 times, span=[0, 1])"
