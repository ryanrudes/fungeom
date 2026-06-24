"""Vec3Signal — the vector instance of the function-with-a-time-hole."""

from __future__ import annotations

from fungeom import Boundary, Instant, Interval, Sampling, Unresolvable, Vec3Signal
from fungeom.values import IntervalValue, SampledSeries


def test_from_samples_and_at() -> None:
    signal = Vec3Signal.from_samples([0.0, 2.0], [[0.0, 0.0, 0.0], [2.0, 20.0, -2.0]])
    sampled = signal.at(1.0).resolve()  # componentwise linear, returns a Vec3 value
    assert sampled.tolist() == [1.0, 10.0, -1.0]
    # the sample bridges back into the static vec3 algebra
    assert signal.at(1.0).norm().resolve() > 0.0


def test_over_and_resample() -> None:
    signal = Vec3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [10, 0, 0], [20, 0, 0]])
    assert signal.over().resolve() == IntervalValue(0.0, 2.0)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    resampled = signal.resample(grid).resolve()
    assert [row[0] for row in resampled.values] == [0.0, 5.0, 10.0, 15.0, 20.0]
    assert not signal.resample(Sampling.at_times([1.0, 9.0])).is_resolvable  # past the domain


def test_partiality() -> None:
    # build-level: bad sampling and value-count mismatch
    assert not Vec3Signal.from_samples([1.0, 0.0], [[0, 0, 0], [1, 1, 1]]).is_resolvable
    assert not Vec3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [1, 1, 1]]).is_resolvable
    # sample-level: off-domain
    signal = Vec3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [1, 1, 1]])
    decision = signal.at(9.0).decide()
    assert isinstance(decision, Unresolvable)
    assert "no data at t=9s" in decision.reason
    # ...unless a boundary is given
    held = Vec3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [1, 2, 3]], outside=Boundary.hold)
    assert held.at(9.0).resolve().tolist() == [1.0, 2.0, 3.0]


def test_value_helpers() -> None:
    signal = Vec3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [1, 1, 1]]).resolve()
    assert isinstance(signal, SampledSeries)
    assert signal.domain == (0.0, 1.0)
    assert [row.tolist() for row in signal.values] == [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
    assert repr(signal) == "SampledSeries(2 samples over [0, 1])"


def test_restrict_and_shift() -> None:
    sig = Vec3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [10, 0, 0], [20, 0, 0]])
    clipped = sig.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    assert clipped.at(0.5).resolve().tolist() == [5.0, 0.0, 0.0]  # reconstructed endpoint
    assert clipped.at(1.0).resolve().tolist() == [10.0, 0.0, 0.0]  # interior preserved
    shifted = sig.shift(2.0)
    assert shifted.over().resolve() == IntervalValue(2.0, 4.0)
    assert shifted.at(3.0).resolve().tolist() == [10.0, 0.0, 0.0]
    assert not sig.restrict(Interval.between(Instant.at(10.0), Instant.at(11.0))).is_resolvable


def test_defined_at() -> None:
    sig = Vec3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [10, 0, 0], [20, 0, 0]])
    assert sig.defined_at(1.0).resolve() is True
    assert sig.defined_at(5.0).resolve() is False


def test_lifting() -> None:
    a = Vec3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [2, 0, 0]])
    b = Vec3Signal.from_samples([0.0, 1.0], [[0, 1, 0], [0, 1, 0]])
    assert (a + b).at(0.5).resolve().tolist() == [1.0, 1.0, 0.0]
    assert (a - b).at(1.0).resolve().tolist() == [2.0, -1.0, 0.0]


def test_dot_lift() -> None:
    # cross-type lift: two Vec3 signals -> a ScalarSignal of their dot product over time
    u = Vec3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [1, 0, 0]])
    v = Vec3Signal.from_samples([0.0, 1.0], [[0, 1, 0], [1, 0, 0]])
    assert u.dot(v).at(0.0).resolve() == 0.0
    assert u.dot(v).at(1.0).resolve() == 1.0


def test_reparameterize_by_warp() -> None:
    from fungeom import TimeWarp

    sig = Vec3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [2, 20, -2]])
    warp = TimeWarp.through([(0.0, 0.0), (1.0, 1.5), (2.0, 2.0)])  # nonlinear, covers [0, 2]
    bent = sig.reparameterize(warp)
    assert bent.over().resolve() == IntervalValue(0.0, 2.0)
    assert bent.at(2.0).resolve().tolist() == [2.0, 20.0, -2.0]
