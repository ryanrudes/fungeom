"""resolve_over — the sanctioned vectorized ndarray readback from the lazy signal graph (P3)."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    Direction3Signal,
    Instant,
    Interval,
    Point3BundleSignal,
    Point3Signal,
    RigidTransform,
    Sampling,
    ScalarBundleSignal,
    ScalarSignal,
    TransformSignal,
    Vec3Signal,
)
from fungeom.core.resolvability import UnresolvableError


def _grid() -> Sampling:
    return Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 3)  # t = 0, 1, 2


def test_plain_signal_readbacks() -> None:
    assert np.allclose(ScalarSignal.from_samples([0, 2], [0, 10]).resolve_over(_grid()), [0, 5, 10])
    assert np.allclose(Vec3Signal.from_samples([0, 2], [[0, 0, 0], [2, 4, 6]]).resolve_over(_grid())[1], [1, 2, 3])
    assert np.allclose(Point3Signal.from_samples([0, 2], [[0, 0, 0], [2, 0, 0]]).resolve_over(_grid())[:, 0], [0, 1, 2])
    assert Direction3Signal.from_samples([0, 2], [[1, 0, 0], [1, 0, 0]]).resolve_over(_grid()).shape == (3, 3)
    poses = TransformSignal.from_samples(
        [0, 2], [RigidTransform.identity(), RigidTransform.from_translation([4, 0, 0])]
    )
    matrices = poses.resolve_over(_grid())
    assert matrices.shape == (3, 4, 4)
    assert np.allclose(matrices[1][:3, 3], [2, 0, 0])  # the interpolated translation


def test_bundle_signal_readback_with_mask() -> None:
    cloud = Point3BundleSignal.from_frames([0, 2], [[[0, 0, 0], [1, 1, 1]], [[2, 0, 0], [1, 1, 1]]], keys=["a", "b"])
    values, mask = cloud.resolve_over(_grid())
    assert values.shape == (3, 2, 3)
    assert mask.shape == (3, 2)
    assert mask.all()  # nothing occluded
    assert np.allclose(values[:, 0, 0], [0, 1, 2])  # marker 'a' x-track
    # a scalar cloud
    sb = ScalarBundleSignal.from_frames([0, 2], [[1.0, 2.0], [3.0, 4.0]], keys=["a", "b"])
    sv, sm = sb.resolve_over(_grid())
    assert sv.shape == (3, 2)
    assert np.allclose(sv[1], [2, 3])


def test_occluded_cells_are_nan_with_false_mask() -> None:
    occ = Point3BundleSignal.from_frames(
        [0, 2], [[[0, 0, 0], [9, 9, 9]], [[2, 0, 0], [9, 9, 9]]], keys=["a", "b"], present=[[True, False], [True, True]]
    )
    values, mask = occ.resolve_over(Sampling.at_times([0.0]))
    assert list(mask[0]) == [True, False]
    assert np.isnan(values[0, 1]).all()  # the occluded marker's cell is nan


def test_resolve_over_raises_off_support() -> None:
    s = ScalarSignal.from_samples([0, 2], [0, 10])
    off = Sampling.at_times([10.0])  # outside the signal's support
    with pytest.raises(UnresolvableError):
        s.resolve_over(off)
