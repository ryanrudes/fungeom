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


def test_derivative_and_norm() -> None:
    import numpy as np

    v = Vec3Signal.from_samples([0.0, 1.0, 2.0], [[0, 0, 0], [3, 4, 0], [6, 8, 0]])
    assert np.allclose(v.derivative().at(1.0).resolve(), [3, 4, 0])  # central difference
    assert v.norm().at(1.0).resolve() == 5.0  # |(3, 4, 0)|
    assert isinstance(Vec3Signal.from_samples([0.0], [[1, 1, 1]]).derivative().decide(), Unresolvable)


def test_transformed_by_rotates_a_free_vector() -> None:
    import numpy as np
    from scipy.spatial.transform import Rotation

    from fungeom import RigidTransform, TransformSignal

    # a pose with a translation: the free vector ignores it (rotation only)
    poses = [RigidTransform.from_rotation(Rotation.from_euler("z", a, degrees=True), [99, 0, 0]) for a in (0, 90)]
    pose = TransformSignal.from_samples([0.0, 2.0], poses)
    v = Vec3Signal.from_samples([0.0, 2.0], [[1, 0, 0], [1, 0, 0]])
    assert np.allclose(v.transformed_by(pose).at(2.0).resolve(), [0, 1, 0], atol=1e-9)


def test_lift_and_map() -> None:
    import numpy as np

    from fungeom import Point3Signal

    pa = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [0, 0, 0]])
    pb = Point3Signal.from_samples([0.0, 2.0], [[3, 4, 0], [6, 8, 0]])
    disp = Vec3Signal.lift([pa, pb], lambda a, b: a.displacement_to(b))  # two Point3Signals → a Vec3Signal
    assert np.allclose(disp.at(2.0).resolve(), [6, 8, 0])
    scaled = Vec3Signal.from_samples([0.0, 2.0], [[1, 0, 0], [1, 0, 0]]).map(lambda v: v.scale(3.0))
    assert np.allclose(scaled.at(0.0).resolve(), [3, 0, 0])


def test_lift_over_sample_disjoint_overlap_is_unresolvable() -> None:
    # two signals whose supports overlap but whose *sample instants* fall outside the overlap:
    # there is no aligned instant to reconstruct from, so the lift is Unresolvable — not a
    # 0-sample Resolvable that crashes on read (the empty-alignment guard)
    a = Vec3Signal.from_samples([0.0, 10.0], [[0, 0, 0], [10, 0, 0]])  # samples at 0, 10
    b = a.restrict(Interval.between(Instant.at(3.0), Instant.at(7.0)))  # support [3,7], samples still 0,10
    summed = a + b  # binary lift (decide_lifted)
    assert isinstance(summed.decide(), Unresolvable)
    assert isinstance(summed.at(5.0).decide(), Unresolvable)  # was an IndexError before the guard
    # the unary lift (decide_lifted_n, via map) hits the same guard
    mapped = b.map(lambda v: v.scale(2.0))
    assert isinstance(mapped.decide(), Unresolvable)
