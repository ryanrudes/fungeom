"""ScalarBundleSignal — a collection of scalars over time, with per-instant folds (the contact spine)."""

from __future__ import annotations

import numpy as np

from fungeom import (
    Interpolation,
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


def test_resolve_over_vectorized_matches_per_instant_and_falls_back() -> None:
    # the dense (T, N) contact-field carrier's vectorized resolve_over equals the per-instant at(t)
    # readback (incl. occlusion + between-sample interp); a non-default kernel defers to the generic path.
    times = np.arange(5) * 0.5
    data = np.random.default_rng(2).standard_normal((5, 3))
    present = np.ones((5, 3), dtype=bool)
    present[2, 0] = False  # occlude marker 0 at t = 1.0
    cloud = ScalarBundleSignal.from_frames(times, data, keys=["a", "b", "c"], present=present)

    for onto_times in (times, times[:-1] + 0.25):  # exact knots + between-sample
        values, mask = cloud.resolve_over(Sampling.at_times(onto_times))
        for i, t in enumerate(onto_times):
            bundle = cloud.at(float(t)).resolve()
            assert np.array_equal(mask[i], [bundle.present(k) for k in bundle.roster])
            for j, key in enumerate(bundle.roster):
                if bundle.present(key):
                    assert np.isclose(values[i, j], bundle.members[key])
                else:
                    assert np.isnan(values[i, j])

    held = ScalarBundleSignal.from_frames(times, data, via=Interpolation.hold)  # fallback → generic
    assert held.resolve_over(Sampling.at_times(times[:-1] + 0.25))[0].shape == (4, 3)


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


def test_folds_propagate_the_source_kernel_and_boundary() -> None:
    from fungeom.primitives.signals.boundary import Boundary
    from fungeom.primitives.signals.interpolation import Interpolation

    # a hold-reconstructed cloud: the fold must read the same way the source does (not snap to linear)
    held = ScalarBundleSignal.from_frames([0.0, 2.0], [[0.0], [10.0]], keys=["a"], via=Interpolation.hold)
    assert held.min().at(1.0).resolve() == held.at(1.0).min().resolve() == 0.0  # held, not linear's 5.0
    # a hold *boundary*: the fold must not shrink the domain (it used to drop the boundary → Unresolvable)
    bounded = ScalarBundleSignal.from_frames([0.0, 2.0], [[0.0], [10.0]], keys=["a"], outside=Boundary.hold)
    assert bounded.min().at(3.0).resolve() == bounded.at(3.0).min().resolve() == 10.0
