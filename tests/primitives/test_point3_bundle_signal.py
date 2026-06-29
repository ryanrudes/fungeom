"""Point3BundleSignal — a point cloud over time (Signal[Bundle[Point3]] by composition)."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    Boundary,
    CoordinateFrame,
    Instant,
    Interpolation,
    Interval,
    Point3,
    Point3BundleSignal,
    Point3Signal,
    Sampling,
    ScalarSignal,
    Unresolvable,
    UnresolvableError,
)
from fungeom.values import CoverageValue, IntervalValue, SampledSeries


def _clip() -> Point3BundleSignal:
    # HEAD moves +x over [0, 2]; LWRIST stays put
    return Point3BundleSignal.from_frames(
        [0.0, 2.0],
        [[[0, 0, 0], [5, 0, 0]], [[10, 0, 0], [5, 0, 0]]],
        keys=["HEAD", "LWRIST"],
    )


def _per_instant(cloud: Point3BundleSignal, onto_times: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ground truth: the per-instant ``at(t)`` readback (dense ``(T, N, 3)`` + present mask)."""
    rows, masks = [], []
    for t in onto_times:
        bundle = cloud.at(float(t)).resolve()
        rows.append([bundle.members[k].coord if bundle.present(k) else [np.nan] * 3 for k in bundle.roster])
        masks.append([bundle.present(k) for k in bundle.roster])
    return np.array(rows, dtype=float), np.array(masks, dtype=bool)


def test_resolve_over_vectorized_matches_per_instant_and_falls_back() -> None:
    # the dense (T, N, 3) carrier's vectorized resolve_over must equal the per-instant at(t) readback
    # bit-for-bit — including occlusion (key-intersection mask) and between-sample interpolation — and
    # defer to the generic path for any reconstruction the shortcut does not model.
    times = np.arange(6) * 0.5  # 0, .5, 1, 1.5, 2, 2.5
    data = np.random.default_rng(0).standard_normal((6, 4, 3))
    present = np.ones((6, 4), dtype=bool)
    present[3, 1] = False  # occlude marker 1 at t = 1.5
    cloud = Point3BundleSignal.from_frames(times, data, present=present)

    for onto_times in (times, times[:-1] + 0.25, times[::2]):  # exact knots, between-sample, knot subset
        values, mask = cloud.resolve_over(Sampling.at_times(onto_times))
        ref_values, ref_mask = _per_instant(cloud, onto_times)
        assert np.array_equal(mask, ref_mask)
        assert np.array_equal(np.isnan(values), np.isnan(ref_values))  # occluded cells are nan on both
        assert np.allclose(values[mask], ref_values[ref_mask])

    # fallbacks (dense_grid_readback → None → generic per-instant path):
    held = Point3BundleSignal.from_frames(times, data, via=Interpolation.hold)  # non-default kernel
    assert held.resolve_over(Sampling.at_times(times[:-1] + 0.25))[0].shape == (5, 4, 3)
    gapped = Point3BundleSignal.from_frames(times, data, max_gap=0.4)  # 0.5 spacing > 0.4 → interior gaps
    assert gapped.resolve_over(Sampling.at_times(times))[1].all()  # exact knots still resolve, all present
    single = Point3BundleSignal.from_frames([1.0], data[:1])  # T = 1, no interval to interpolate
    assert single.resolve_over(Sampling.at_times([1.0]))[0].shape == (1, 4, 3)
    with pytest.raises(UnresolvableError):
        cloud.resolve_over(Sampling.at_times([times[-1] + 1.0]))  # off-domain target → generic raises
    with pytest.raises(UnresolvableError):
        cloud.resolve_over(Sampling.at_times([1.0, 0.0]))  # an Unresolvable (non-monotonic) onto


def _occluded_clip() -> Point3BundleSignal:
    # A present throughout; B occluded at frame 1; C present only at frame 0.
    return Point3BundleSignal.from_frames(
        [0.0, 1.0, 2.0, 3.0],
        [
            [[0, 0, 0], [0, 1, 0], [0, 2, 0]],
            [[1, 0, 0], [9, 9, 9], [9, 9, 9]],
            [[2, 0, 0], [2, 1, 0], [9, 9, 9]],
            [[3, 0, 0], [3, 1, 0], [9, 9, 9]],
        ],
        keys=["A", "B", "C"],
        present=[
            [True, True, True],
            [True, False, False],
            [True, True, False],
            [True, True, False],
        ],
    )


def _agree(left: Point3, right: Point3) -> bool:
    """Whether two Point3 resolvers agree — both Unresolvable, or equal coordinates."""
    ld, rd = left.decide(), right.decide()
    if isinstance(ld, Unresolvable) or isinstance(rd, Unresolvable):
        return isinstance(ld, Unresolvable) and isinstance(rd, Unresolvable)
    return bool(np.allclose(ld.value.coord, rd.value.coord))


def test_construction_and_at_bridges_to_bundle_algebra() -> None:
    clip = _clip()
    assert isinstance(clip.resolve(), SampledSeries)
    assert clip.over().resolve() == IntervalValue(0.0, 2.0)
    mid = clip.at(1.0)  # a Point3Bundle — the static collection algebra is available
    assert np.allclose(mid.at("HEAD").resolve().coord, [5, 0, 0])  # interpolated frame
    assert np.allclose(mid.centroid().resolve().coord, [5, 0, 0])
    assert mid.count().resolve() == 2.0
    assert np.allclose(clip.at(2.0).at("HEAD").resolve().coord, [10, 0, 0])  # exact frame


def test_occlusion_mask_falls_out_of_the_blend() -> None:
    # LWRIST is occluded at frame 1 (present only at frame 0)
    occ = Point3BundleSignal.from_frames(
        [0.0, 2.0],
        [[[0, 0, 0], [5, 0, 0]], [[10, 0, 0], [0, 0, 0]]],
        keys=["HEAD", "LWRIST"],
        present=[[True, True], [True, False]],
    )
    assert np.allclose(occ.at(0.0).at("LWRIST").resolve().coord, [5, 0, 0])  # present at frame 0
    assert isinstance(occ.at(2.0).at("LWRIST").decide(), Unresolvable)  # absent at the exact frame
    # interpolating across the dropout leaves LWRIST absent (only one bracket has it)…
    assert isinstance(occ.at(1.0).at("LWRIST").decide(), Unresolvable)
    # …but HEAD, present in both brackets, still interpolates
    assert np.allclose(occ.at(1.0).at("HEAD").resolve().coord, [5, 0, 0])
    assert occ.at(1.0).count().resolve() == 1.0
    # the interpolated cloud keeps the full DECLARED roster (LWRIST is absent, not unknown)
    assert occ.at(1.0).resolve().roster == ("HEAD", "LWRIST")


def test_exact_interior_sample_returns_the_full_frame() -> None:
    # An exact sample must be that frame's cloud — never routed through the support-changing
    # blend. LWRIST is occluded at frame 0 but present at frames 1 and 2; querying the exact
    # interior sample t=1.0 must return it (the commuting square holds at exact samples).
    occ = Point3BundleSignal.from_frames(
        [0.0, 1.0, 2.0],
        [[[0, 0, 0], [9, 9, 9]], [[10, 0, 0], [5, 0, 0]], [[20, 0, 0], [5, 0, 0]]],
        keys=["HEAD", "LWRIST"],
        present=[[True, False], [True, True], [True, True]],
    )
    assert np.allclose(occ.at(1.0).at("LWRIST").resolve().coord, [5, 0, 0])  # exact interior, present
    assert occ.at(1.0).count().resolve() == 2.0
    assert isinstance(occ.at(0.5).at("LWRIST").decide(), Unresolvable)  # but interpolation across the dropout drops it


def test_inherited_time_ops() -> None:
    clip = _clip()
    assert clip.shift(5.0).over().resolve() == IntervalValue(5.0, 7.0)
    clipped = clip.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    assert np.allclose(clip.resample(grid).at(1.0).at("HEAD").resolve().coord, [5, 0, 0])


def test_partiality() -> None:
    clip = _clip()
    # off-domain sample
    assert isinstance(clip.at(9.0).decide(), Unresolvable)
    # frame/time count mismatch (3 frames, 2 times)
    mismatch = Point3BundleSignal.from_frames([0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]], [[2, 0, 0]]])
    decision = mismatch.decide()
    assert isinstance(decision, Unresolvable)
    assert "3 frames for 2 sample times" in decision.reason
    # an ungrounded frame makes the whole signal Unresolvable (build-time grounding)
    detached = Point3BundleSignal.from_frames(
        [0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]]], frame=CoordinateFrame.detached("loose")
    )
    assert isinstance(detached.decide(), Unresolvable)


def test_key_projects_one_marker_trajectory() -> None:
    # key(k) is the entity-axis slice: one marker across all time, as a real Point3Signal.
    head = _clip().key("HEAD")
    assert isinstance(head, Point3Signal)
    assert head.over().resolve() == IntervalValue(0.0, 2.0)
    assert np.allclose(head.at(0.0).resolve().coord, [0, 0, 0])
    assert np.allclose(head.at(1.0).resolve().coord, [5, 0, 0])  # interpolated
    assert np.allclose(head.at(2.0).resolve().coord, [10, 0, 0])


def test_key_commuting_square_holds_on_the_support() -> None:
    # The crux of the composition: at(t).at(k) == key(k).at(t) everywhere both are read,
    # across exact frames, interior interpolation, entity gaps, and off-domain — for every key.
    field = _occluded_clip()
    times = [-1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    for k in ("A", "B", "C"):
        track = field.key(k)
        for t in times:
            assert _agree(field.at(t).at(k), track.at(t)), f"mismatch at key={k!r}, t={t}"


def test_key_support_gaps_at_occlusions() -> None:
    field = _occluded_clip()
    # A is present at every frame → one unbroken span
    assert field.key("A").support().resolve() == CoverageValue((IntervalValue(0.0, 3.0),))
    # B drops out at frame 1 → the support splits: the exact point at t=0, then the run [2, 3]
    b = field.key("B")
    assert b.support().resolve() == CoverageValue((IntervalValue(0.0, 0.0), IntervalValue(2.0, 3.0)))
    assert np.allclose(b.at(0.0).resolve().coord, [0, 1, 0])  # the isolated exact frame
    assert isinstance(b.at(1.0).decide(), Unresolvable)  # in the entity gap
    assert isinstance(b.at(1.5).decide(), Unresolvable)
    assert np.allclose(b.at(2.5).resolve().coord, [2.5, 1, 0])  # interpolates inside the later span
    # C is present only at frame 0 → a single degenerate point span
    assert field.key("C").support().resolve() == CoverageValue((IntervalValue(0.0, 0.0),))


def test_key_enables_the_trajectory_algebra() -> None:
    # Because the slice is an ordinary Point3Signal, the whole signal algebra composes:
    # the time-varying separation of two markers is a ScalarSignal. (The lift aligns on
    # the markers' sample instants, so it is exact there — sampled at every frame here.)
    field = Point3BundleSignal.from_frames(
        [0.0, 1.0, 2.0],
        [
            [[0, 0, 0], [5, 0, 0]],
            [[5, 0, 0], [5, 0, 0]],
            [[10, 0, 0], [5, 0, 0]],
        ],
        keys=["HEAD", "LWRIST"],
    )
    separation = field.key("HEAD").distance_to(field.key("LWRIST"))
    assert isinstance(separation, ScalarSignal)
    assert separation.at(0.0).resolve() == 5.0
    assert separation.at(1.0).resolve() == 0.0  # HEAD coincides with LWRIST at this frame
    assert separation.at(2.0).resolve() == 5.0


def test_key_partiality() -> None:
    field = _clip()
    # a key that was never declared in the cloud's roster
    assert "not in the cloud signal's roster" in field.key("NOPE").decide().reason
    # a fully-occluded marker has no trajectory to project
    occ = Point3BundleSignal.from_frames([0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]]], keys=["X"], present=[[False], [False]])
    assert "never present" in occ.key("X").decide().reason
    # source partiality propagates (a frame/time count mismatch)
    mismatch = Point3BundleSignal.from_frames([0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]], [[2, 0, 0]]])
    assert isinstance(mismatch.key(0).decide(), Unresolvable)


def test_key_support_splits_at_a_temporal_gap() -> None:
    # A marker present at all frames, but the cloud has a TEMPORAL dropout (max_gap): the
    # trajectory must split there too — distinct from the entity-gap path (here the present
    # frames are adjacent in index but separated in time). And the square holds in the gap.
    field = Point3BundleSignal.from_frames(
        [0.0, 1.0, 5.0, 6.0],
        [[[0, 0, 0]], [[1, 0, 0]], [[5, 0, 0]], [[6, 0, 0]]],
        keys=["M"],
        max_gap=2.0,
    )
    track = field.key("M")
    assert track.support().resolve() == CoverageValue((IntervalValue(0.0, 1.0), IntervalValue(5.0, 6.0)))
    # commuting square inside the temporal gap: both sides Unresolvable
    assert isinstance(field.at(3.0).at("M").decide(), Unresolvable)
    assert isinstance(track.at(3.0).decide(), Unresolvable)
    assert np.allclose(track.at(5.5).resolve().coord, [5.5, 0, 0])  # interpolates inside the later span


def test_key_refuses_non_default_reconstruction() -> None:
    # The commuting square is proven only for linear interpolation + undefined boundary;
    # under hold/nearest or hold/wrap the projection cannot mirror the cloud, so key()
    # is Unresolvable (refuse rather than silently disagree) — not silently wrong.
    frames = [[[0, 0, 0]], [[1, 0, 0]]]
    held_kernel = Point3BundleSignal.from_frames([0.0, 1.0], frames, keys=["M"], via=Interpolation.hold)
    held_edge = Point3BundleSignal.from_frames([0.0, 1.0], frames, keys=["M"], outside=Boundary.hold)
    for signal in (held_kernel, held_edge):
        decision = signal.key("M").decide()
        assert isinstance(decision, Unresolvable)
        assert "default reconstruction" in decision.reason


def test_transformed_by_a_moving_pose() -> None:
    from scipy.spatial.transform import Rotation

    from fungeom import Point3BundleSignal, RigidTransform, TransformSignal, Unresolvable

    poses = [
        RigidTransform.from_rotation(Rotation.from_euler("z", a, degrees=True), [tx, 0, 0])
        for a, tx in [(0, 0), (90, 10)]
    ]
    pose = TransformSignal.from_samples([0.0, 2.0], poses)
    cloud = Point3BundleSignal.from_frames(
        [0.0, 2.0], [[[1, 0, 0], [0, 1, 0]], [[1, 0, 0], [0, 1, 0]]], keys=["a", "b"]
    )
    world = cloud.transformed_by(pose)
    assert np.allclose(world.at(2.0).at("a").resolve().coord, [10, 1, 0], atol=1e-9)  # rot90·(1,0,0)+(10,0,0)
    assert np.allclose(world.at(2.0).at("b").resolve().coord, [9, 0, 0], atol=1e-9)  # rot90·(0,1,0)+(10,0,0)
    assert isinstance(world.at(5.0).decide(), Unresolvable)  # off the pose's support


def test_transformed_by_per_joint_poses() -> None:
    from fungeom import Point3BundleSignal, Transform, TransformBundleSignal

    times = [0.0, 2.0]
    poses = TransformBundleSignal.from_frames(
        times,
        [
            [Transform.translation((0, 0, 0)), Transform.translation((0, 0, 0))],
            [Transform.translation((10, 0, 0)), Transform.translation((0, 10, 0))],
        ],
        keys=["a", "b"],
    )
    cloud = Point3BundleSignal.from_frames(times, [[[1, 0, 0], [0, 1, 0]], [[1, 0, 0], [0, 1, 0]]], keys=["a", "b"])
    world = cloud.transformed_by(poses)  # each marker by its own joint's moving pose
    assert np.allclose(world.at(2.0).at("a").resolve().coord, [11, 0, 0])
    assert np.allclose(world.at(2.0).at("b").resolve().coord, [0, 11, 0])


def test_centroid_is_the_cloud_centre_track() -> None:
    cloud = Point3BundleSignal.from_frames(
        [0.0, 2.0], [[[0, 0, 0], [2, 0, 0]], [[0, 0, 0], [4, 0, 0]]], keys=["a", "b"]
    )
    assert np.allclose(cloud.centroid().at(0.0).resolve().coord, [1, 0, 0])  # mean of (0,0,0),(2,0,0)
    assert np.allclose(cloud.centroid().at(2.0).resolve().coord, [2, 0, 0])  # mean of (0,0,0),(4,0,0)
    # a frame with no present member makes the centroid track Unresolvable
    occluded = Point3BundleSignal.from_frames(
        [0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]]], keys=["a"], present=[[False], [True]]
    )
    assert isinstance(occluded.centroid().decide(), Unresolvable)
