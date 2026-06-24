"""TransformSignal — pose interpolation on SE(3) (slerp + lerp)."""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom import Instant, Interval, Sampling, TimeMap, TransformSignal, Unresolvable
from fungeom.values import IntervalValue, RigidTransform, SampledSeries


def _pose(angle_deg: float, translation: list[float]) -> RigidTransform:
    return RigidTransform.from_rotation(Rotation.from_euler("z", angle_deg, degrees=True), translation)


def test_slerp_and_lerp() -> None:
    signal = TransformSignal.from_samples([0.0, 1.0], [_pose(0, [0, 0, 0]), _pose(90, [2, 0, 0])])
    mid = signal.at(0.5).resolve()
    assert np.allclose(mid.translation, [1.0, 0.0, 0.0])  # translation lerps
    assert np.isclose(Rotation.from_matrix(mid.rotation).magnitude(), np.pi / 4)  # rotation slerps


def test_opposed_orientation_is_unresolvable() -> None:
    signal = TransformSignal.from_samples([0.0, 1.0], [_pose(0, [0, 0, 0]), _pose(180, [0, 0, 0])])
    assert signal.is_resolvable
    decision = signal.at(0.5).decide()
    assert isinstance(decision, Unresolvable)
    assert "opposed orientations" in decision.reason


def test_at_bridges_to_transform_algebra() -> None:
    signal = TransformSignal.from_samples([0.0, 1.0], [_pose(0, [1, 0, 0]), _pose(0, [3, 0, 0])])
    # the sample is a real Transform, so the static SE(3) algebra is available
    composed = signal.at(0.5).inverse().resolve()
    assert np.allclose(composed.translation, [-2.0, 0.0, 0.0])


def test_reparameterize() -> None:
    # the same write-once core op works on the SE(3) signal unchanged
    signal = TransformSignal.from_samples([0.0, 1.0], [_pose(0, [0, 0, 0]), _pose(0, [2, 0, 0])])
    shifted = signal.reparameterize(TimeMap.shift(10.0))
    assert shifted.over().resolve() == IntervalValue(10.0, 11.0)
    assert np.allclose(shifted.at(10.5).resolve().translation, [1.0, 0.0, 0.0])


def test_reparameterize_by_warp() -> None:
    from fungeom import TimeWarp

    signal = TransformSignal.from_samples([0.0, 1.0], [_pose(0, [0, 0, 0]), _pose(0, [2, 0, 0])])
    warp = TimeWarp.through([(0.0, 0.0), (0.5, 0.2), (1.0, 1.0)])  # nonlinear, covers [0, 1]
    bent = signal.reparameterize(warp)
    assert bent.over().resolve() == IntervalValue(0.0, 1.0)
    assert np.allclose(bent.at(1.0).resolve().translation, [2.0, 0.0, 0.0])  # last sample carries


def test_over_resample_and_off_domain() -> None:
    signal = TransformSignal.from_samples(
        [0.0, 1.0, 2.0], [_pose(0, [0, 0, 0]), _pose(30, [1, 0, 0]), _pose(60, [2, 0, 0])]
    )
    assert signal.over().resolve() == IntervalValue(0.0, 2.0)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 3)
    assert isinstance(signal.resample(grid).resolve(), SampledSeries)
    assert isinstance(signal.at(9.0).decide(), Unresolvable)  # off-domain


def test_restrict_and_shift() -> None:
    sig = TransformSignal.from_samples(
        [0.0, 1.0, 2.0], [_pose(0, [0, 0, 0]), _pose(45, [1, 0, 0]), _pose(90, [2, 0, 0])]
    )
    clipped = sig.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    assert np.allclose(clipped.at(1.0).resolve().translation, [1.0, 0.0, 0.0])  # interior preserved
    shifted = sig.shift(2.0)
    assert shifted.over().resolve() == IntervalValue(2.0, 4.0)
    assert not sig.restrict(Interval.between(Instant.at(10.0), Instant.at(11.0))).is_resolvable


def test_defined_at() -> None:
    sig = TransformSignal.from_samples(
        [0.0, 1.0, 2.0], [_pose(0, [0, 0, 0]), _pose(45, [1, 0, 0]), _pose(90, [2, 0, 0])]
    )
    assert sig.defined_at(1.0).resolve() is True
    assert sig.defined_at(5.0).resolve() is False
