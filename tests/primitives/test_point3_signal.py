"""Point3Signal — a point trajectory, with frame grounding as a second partiality axis."""

from __future__ import annotations

import numpy as np

from fungeom import CoordinateFrame, Instant, Interval, Point3, Point3Signal, Sampling, Unresolvable
from fungeom.values import IntervalValue, SampledSeries


def test_from_samples_and_at() -> None:
    signal = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [10, 0, 0]])
    assert np.allclose(signal.at(1.0).resolve().coord, [5.0, 0.0, 0.0])  # world-space lerp


def test_at_bridges_to_point_algebra() -> None:
    signal = Point3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [3, 4, 0]])
    # the sample is a real Point3, so distances/directions are available downstream
    assert signal.at(1.0).distance_to(Point3.at(0, 0, 0)).resolve() == 5.0


def test_ungrounded_frame_is_unresolvable() -> None:
    # the second partiality axis: a point on a detached frame can't be world-anchored
    loose = Point3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [1, 0, 0]], frame=CoordinateFrame.detached("cam"))
    assert not loose.is_resolvable  # build-level: grounding fails before sampling
    decision = loose.at(0.5).decide()
    assert isinstance(decision, Unresolvable)
    assert "not grounded" in decision.reason


def test_over_resample_and_off_domain() -> None:
    signal = Point3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [2, 0, 0], [4, 0, 0]])
    assert signal.over().resolve() == IntervalValue(0.0, 2.0)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    resampled = signal.resample(grid).resolve()
    assert isinstance(resampled, SampledSeries)
    assert [round(float(p.coord[0]), 1) for p in resampled.values] == [0.0, 1.0, 2.0, 3.0, 4.0]
    assert isinstance(signal.at(9.0).decide(), Unresolvable)  # off-domain


def test_build_level_count_mismatch() -> None:
    assert not Point3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [1, 1, 1]]).is_resolvable


def test_restrict_and_shift() -> None:
    sig = Point3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [10, 0, 0], [20, 0, 0]])
    clipped = sig.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    assert np.allclose(clipped.at(0.5).resolve().coord, [5.0, 0.0, 0.0])  # reconstructed endpoint
    shifted = sig.shift(2.0)
    assert shifted.over().resolve() == IntervalValue(2.0, 4.0)
    assert np.allclose(shifted.at(3.0).resolve().coord, [10.0, 0.0, 0.0])
    assert not sig.restrict(Interval.between(Instant.at(10.0), Instant.at(11.0))).is_resolvable


def test_defined_at() -> None:
    sig = Point3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [10, 0, 0], [20, 0, 0]])
    assert sig.defined_at(1.0).resolve() is True
    assert sig.defined_at(5.0).resolve() is False


def test_sampled_parity_with_explicit_sampling() -> None:
    # parity with the other facades: build from an explicit Sampling (not just from_samples)
    signal = Point3Signal.sampled(Sampling.at_times([0.0, 2.0]), [[0, 0, 0], [10, 0, 0]])
    assert np.allclose(signal.at(1.0).resolve().coord, [5.0, 0.0, 0.0])


def test_distance_and_displacement_lift() -> None:
    # the distance / displacement between two moving points, as signals over time
    a = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [0, 0, 0]])  # stays at the origin
    b = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [6, 8, 0]])  # moves to (6, 8, 0)
    assert a.distance_to(b).at(1.0).resolve() == 5.0  # midpoint (3, 4, 0)
    assert a.distance_to(b).at(2.0).resolve() == 10.0
    assert np.allclose(a.displacement_to(b).at(1.0).resolve(), [3.0, 4.0, 0.0])
