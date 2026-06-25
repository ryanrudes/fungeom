"""ScalarBundleSignal — a collection of scalars over time, with per-instant folds (the contact spine)."""

from __future__ import annotations

import numpy as np

from fungeom import (
    Interval,
    Instant,
    Point3BundleSignal,
    Sampling,
    ScalarBundle,
    ScalarBundleSignal,
    TimeMap,
    TimeWarp,
    Unresolvable,
)
from fungeom.values import CoverageValue, IntervalValue, SampledSeries


def _clearances() -> ScalarBundleSignal:
    # three markers' clearance over [0, 2]: marker 'b' dips below zero
    return ScalarBundleSignal.from_frames([0.0, 2.0], [[2.0, 1.0, 3.0], [0.5, -1.0, 1.0]], keys=["a", "b", "c"])


def test_construction_and_at() -> None:
    clear = _clearances()
    assert isinstance(clear.resolve(), SampledSeries)
    assert isinstance(clear.at(0.0), ScalarBundle)
    assert clear.at(0.0).at("b").resolve() == 1.0
    assert clear.at(1.0).at("b").resolve() == 0.0  # the key-by-key lerp


def test_folds_reduce_per_instant() -> None:
    clear = _clearances()
    assert clear.min().at(0.0).resolve() == 1.0
    assert clear.min().at(2.0).resolve() == -1.0
    assert clear.max().at(2.0).resolve() == 1.0
    assert clear.mean().at(0.0).resolve() == 2.0  # (2 + 1 + 3) / 3
    assert clear.sum().at(2.0).resolve() == 0.5  # 0.5 - 1 + 1
    assert clear.count().at(0.0).resolve() == 3.0


def test_the_contact_spine() -> None:
    # the headline: per-marker clearance → min over the footprint → threshold → contact intervals
    clear = _clearances()
    min_clearance = clear.min()  # samples (0, 1.0) and (2, -1.0) → crosses 0 at t=1
    assert min_clearance.at(1.0).resolve() == 0.0
    any_in_contact = min_clearance.lt(0.0)  # a BoolSignal
    assert any_in_contact.when_true().resolve() == CoverageValue((IntervalValue(1.0, 2.0),))


def test_full_spine_from_a_fitted_plane() -> None:
    # fit a moving plane to a cloud, take a foot cloud's clearance, fold to min, threshold
    ground = Point3BundleSignal.from_frames(
        [0.0, 2.0], [[[0, 0, 0], [2, 0, 0], [0, 2, 0]], [[0, 0, 0], [2, 0, 0], [0, 2, 0]]]
    )
    plane = ground.fit_plane()
    foot = Point3BundleSignal.from_frames(
        [0.0, 2.0], [[[0, 0, 1], [1, 1, 1]], [[0, 0, -0.5], [1, 1, 0.5]]], keys=["heel", "toe"]
    )
    clearances = plane.signed_distance(foot)  # → ScalarBundleSignal
    assert isinstance(clearances, ScalarBundleSignal)
    min_clear = clearances.min()
    assert np.isclose(abs(min_clear.at(0.0).resolve()), 1.0)
    assert np.isclose(min_clear.at(2.0).resolve(), -0.5)
    # min clearance ≤ 0 (some corner touching) over [4/3, 2]
    contact = min_clear.le(0.0).when_true().resolve()
    assert np.isclose(contact.intervals[0].start, 4 / 3)
    assert np.isclose(contact.intervals[0].end, 2.0)


def test_frame_count_mismatch_is_unresolvable() -> None:
    mismatch = ScalarBundleSignal.from_frames([0.0, 1.0, 2.0], [[1.0], [2.0]])  # 2 frames, 3 times
    decision = mismatch.decide()
    assert isinstance(decision, Unresolvable)
    assert "2 frames for 3 sample times" in decision.reason


def test_occluded_frame_makes_a_fold_unresolvable() -> None:
    occ = ScalarBundleSignal.from_frames([0.0, 1.0], [[1.0], [2.0]], keys=["a"], present=[[False], [True]])
    decision = occ.min().decide()
    assert isinstance(decision, Unresolvable)
    assert "fold is undefined at a frame" in decision.reason
    assert occ.count().at(0.0).resolve() == 0.0  # count is total — zero over the occluded frame


def test_inherited_time_ops() -> None:
    clear = _clearances()
    assert clear.shift(5.0).over().resolve() == IntervalValue(5.0, 7.0)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    assert clear.resample(grid).min().at(1.0).resolve() == 0.0
    clipped = clear.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    assert clear.reparameterize(TimeMap.identity()).min().at(1.0).resolve() == 0.0  # affine path
    warped = clear.reparameterize(TimeWarp.through([(0.0, 0.0), (2.0, 4.0)]))  # warp path
    assert warped.over().resolve() == IntervalValue(0.0, 4.0)
