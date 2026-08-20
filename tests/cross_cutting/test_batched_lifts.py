"""The member axis batches — and decides exactly what the per-member path decided.

A cloud measured against a moving carrier (``FaceSignal.clearance`` / ``PlaneSignal.signed_distance``)
used to build one resolver per member per instant, so asking for a *fold* of that field — strictly
less data than the field itself — cost about fifty times more than reading the field back. The
member axis is now answered in arrays.

These tests pin the part that matters: batching moved no decision. The batched value-type ``_block``
methods are checked against the scalar ones they replace with ``array_equal`` (not ``allclose``),
the acceptance is counted rather than timed, and the fold's *reconstruction* semantics — fold at the
source's knots, then interpolate, which is **not** the same as interpolating then folding — are
pinned against the tempting rewrite that would silently change every off-knot answer.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from fungeom import (
    Direction3,
    Face,
    FaceSignal,
    Plane,
    PlaneValue,
    Point3,
    Point2,
    Point3BundleSignal,
    Region2,
    Region2Value,
    RigidTransform,
    Sampling,
    ScalarBundleSignal,
    TransformSignal,
    Resolvable,
    Unresolvable,
    UnresolvableError,
)
from fungeom.primitives.face.value import FaceValue
from fungeom.primitives.region2.value import point_in_rings
from fungeom.primitives.vec2.value import as_vec2
from fungeom.primitives.vec3.value import as_vec3

_SQUARE = np.array([[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]])
_L = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0], [1.0, 2.0], [0.0, 2.0]])  # non-convex
_OUTER = np.array([[-3.0, -3.0], [3.0, -3.0], [3.0, 3.0], [-3.0, 3.0]])
_HOLE = np.array([[-1.0, -1.0], [-1.0, 1.0], [1.0, 1.0], [1.0, -1.0]])  # clockwise → a hole

_SHAPES = {"square": (_SQUARE,), "non-convex": (_L,), "with a hole": (_OUTER, _HOLE)}


def _probe_points(rings: tuple[np.ndarray, ...], seed: int = 3) -> np.ndarray:
    """Random chart points plus every vertex and edge midpoint — the boundary cases on the nose."""
    rng = np.random.default_rng(seed)
    vertices = np.vstack(rings)
    midpoints = np.vstack([(r[i] + r[(i + 1) % len(r)]) / 2 for r in rings for i in range(len(r))])
    return np.vstack([rng.uniform(-4.0, 4.0, (500, 2)), vertices, midpoints])


# --- the batched value-type paths are the scalar ones, bit for bit -------------------------------


@pytest.mark.parametrize("name", list(_SHAPES))
def test_contains_block_is_bit_identical_to_contains(name: str) -> None:
    region = Region2Value(rings=_SHAPES[name])
    uv = _probe_points(region.rings)
    per_point = np.array([point_in_rings(region.rings, as_vec2(p)) for p in uv])
    assert np.array_equal(region.contains_block(uv), per_point)


@pytest.mark.parametrize("name", list(_SHAPES))
def test_nearest_boundary_block_is_bit_identical_to_nearest_boundary_point(name: str) -> None:
    region = Region2Value(rings=_SHAPES[name])
    uv = _probe_points(region.rings)
    per_point = np.array([region.nearest_boundary_point(as_vec2(p)) for p in uv])
    assert np.array_equal(region.nearest_boundary_block(uv), per_point)


def test_nearest_boundary_block_rejects_the_empty_region() -> None:
    with pytest.raises(ValueError, match="no boundary"):
        Region2Value(rings=()).nearest_boundary_block(np.zeros((2, 2)))


def test_plane_chart_blocks_are_bit_identical_to_the_scalar_chart() -> None:
    plane = PlaneValue(point=[0.3, -0.2, 0.7], normal=as_vec3([0.2, 0.5, 0.84]) / np.linalg.norm([0.2, 0.5, 0.84]))
    rng = np.random.default_rng(11)
    points = rng.uniform(-4.0, 4.0, (500, 3))
    assert np.array_equal(plane.to_local_block(points), np.array([plane.to_local(as_vec3(p)) for p in points]))
    uv = rng.uniform(-4.0, 4.0, (500, 2))
    assert np.array_equal(plane.embed_block(uv), np.array([plane.embed(as_vec2(c)) for c in uv]))


@pytest.mark.parametrize("name", list(_SHAPES))
def test_face_clearance_block_is_bit_identical_to_clearance(name: str) -> None:
    plane = PlaneValue(point=[0.3, -0.2, 0.7], normal=as_vec3([0.2, 0.5, 0.84]) / np.linalg.norm([0.2, 0.5, 0.84]))
    face = FaceValue(plane=plane, region=Region2Value(rings=_SHAPES[name]))
    points = np.random.default_rng(13).uniform(-4.0, 4.0, (800, 3))
    assert np.array_equal(face.clearance_block(points), np.array([face.clearance(as_vec3(p)) for p in points]))
    assert np.array_equal(face.closest_point_block(points), np.array([face.closest_point(as_vec3(p)) for p in points]))


# --- the moving-patch clearance field ------------------------------------------------------------

_FRAMES, _POINTS = 24, 40
_TIMES = np.linspace(0.0, 1.0, _FRAMES)
_CLOUD = np.random.default_rng(17).uniform(-3.0, 3.0, (_FRAMES, _POINTS, 3))


def _moving_poses() -> np.ndarray:
    """A genuinely rotating *and* translating pose stack — an identity pose hides reassociation."""
    matrices = np.tile(np.eye(4), (_FRAMES, 1, 1))
    angles = np.stack([_TIMES * 1.1, _TIMES * 0.7, _TIMES * 0.3], axis=-1)
    matrices[:, :3, :3] = Rotation.from_euler("xyz", angles).as_matrix()
    matrices[:, :3, 3] = np.stack([_TIMES * 0.5, _TIMES * -0.3, _TIMES * 0.9], axis=-1)
    return matrices


def _patch() -> Face:
    plane = Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1))
    # non-convex on purpose: the clamp has somewhere to go wrong that a convex footprint hides
    return Face.on(plane, Region2.polygon([Point2.at(float(u), float(v)) for u, v in _L]))


def _clearance_field() -> Any:
    surface = FaceSignal.of(_patch(), TransformSignal.from_matrices(_TIMES, _moving_poses()))
    return surface.clearance(Point3BundleSignal.from_frames(_TIMES, _CLOUD))


def _decided_grid(signal: Any) -> np.ndarray:
    frames = signal.resolve().values
    return np.array([[frame.members[key] for key in frame.roster] for frame in frames])


def test_clearance_decide_is_bit_identical_to_the_per_point_algebra() -> None:
    """The batched decide re-derived independently, one point at a time through the static algebra."""
    faces = FaceSignal.of(_patch(), TransformSignal.from_matrices(_TIMES, _moving_poses())).resolve().values
    expected = np.array([[face.clearance(as_vec3(p)) for p in _CLOUD[i]] for i, face in enumerate(faces)])
    assert np.array_equal(_decided_grid(_clearance_field()), expected)


def test_clearance_decide_and_resolve_over_agree_bit_for_bit() -> None:
    """One algorithm, not two that round to the same place — the readback *is* the decided field."""
    values, mask = _clearance_field().resolve_over(Sampling.at_times(_TIMES))
    assert mask.all()
    assert np.array_equal(values, _decided_grid(_clearance_field()))


def test_plane_signed_distance_decide_and_resolve_over_agree_bit_for_bit() -> None:
    def field() -> Any:
        square = np.tile(np.array([[-1.0, -1.0, 0.0], [1.0, -1.0, 0.0], [1.0, 1.0, 0.0]]), (_FRAMES, 1, 1))
        plane = Point3BundleSignal.from_frames(_TIMES, square).fit_plane(tolerance=1e-9)
        return plane.signed_distance(Point3BundleSignal.from_frames(_TIMES, _CLOUD))

    values, _ = field().resolve_over(Sampling.at_times(_TIMES))
    assert np.array_equal(values, _decided_grid(field()))


def test_a_fold_costs_no_per_point_trip_through_the_static_algebra(monkeypatch: pytest.MonkeyPatch) -> None:
    """The acceptance, counted rather than timed: folding the field builds no per-member clearance."""
    calls = 0
    original = FaceValue.clearance

    def counted(self: FaceValue, p: Any) -> float:
        nonlocal calls
        calls += 1
        return float(original(self, p))

    monkeypatch.setattr(FaceValue, "clearance", counted)
    _clearance_field().min().resolve_over(Sampling.at_times(_TIMES))
    assert calls == 0  # it was _FRAMES * _POINTS


# --- the folds still mean what they meant --------------------------------------------------------


@pytest.mark.parametrize("kind", ["min", "max", "sum", "mean", "count"])
def test_folds_are_bit_identical_to_reducing_the_decided_frames(kind: str) -> None:
    grid = _decided_grid(_clearance_field())
    # Reduced the way the fold does: Python's sequential ``sum`` over the frame's plain floats.
    # numpy's pairwise reduction — and even ``sum`` over ``np.float64`` — associates differently and
    # lands on different bits, which is the whole reason this asserts equality rather than closeness.
    totals = np.array([float(sum([float(value) for value in row])) for row in grid])
    expected = {
        "min": grid.min(axis=1),
        "max": grid.max(axis=1),
        "sum": totals,
        "mean": totals / grid.shape[1],
        "count": np.full(grid.shape[0], float(grid.shape[1])),
    }[kind]
    folded = getattr(_clearance_field(), kind)().resolve_over(Sampling.at_times(_TIMES))
    assert np.array_equal(folded, expected)


def test_a_fold_reconstructs_between_knots_rather_than_folding_a_reconstruction() -> None:
    """Fold at the source's own instants, *then* interpolate — not the other way round.

    The tempting rewrite (read the bundle back over the target grid, then reduce in arrays) is a
    different function wherever a target falls between the source's samples: here two members
    cross, so the minimum of the interpolated cloud is 5.0 while the interpolation of the
    per-knot minima — what ``min()`` has always meant — is 0.0.
    """
    signal = ScalarBundleSignal.from_frames([0.0, 1.0], np.array([[0.0, 10.0], [10.0, 0.0]]))
    assert signal.min().at(0.5).resolve() == 0.0
    assert min(signal.at(0.5).resolve().members.values()) == 5.0

    onto = Sampling.at_times([0.0, 0.5, 1.0])
    assert np.array_equal(signal.min().resolve_over(onto), np.array([0.0, 0.0, 0.0]))
    values, mask = ScalarBundleSignal.from_frames([0.0, 1.0], np.array([[0.0, 10.0], [10.0, 0.0]])).resolve_over(onto)
    assert np.array_equal(np.where(mask, values, np.inf).min(axis=1), np.array([0.0, 5.0, 0.0]))


# --- partiality is untouched ---------------------------------------------------------------------


def _empty_patch_field() -> Any:
    empty = FaceSignal.of(
        Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty),
        TransformSignal.from_samples([0.0, 1.0], [RigidTransform.identity(), RigidTransform.identity()]),
    )
    return empty.clearance(Point3BundleSignal.from_frames([0.0, 1.0], np.zeros((2, 3, 3))))


def test_an_empty_patch_has_no_surface_to_measure_to() -> None:
    decided = _empty_patch_field().decide()
    assert isinstance(decided, Unresolvable)
    assert "empty face" in decided.reason
    assert isinstance(_empty_patch_field().min().decide(), Unresolvable)
    with pytest.raises(UnresolvableError):
        _empty_patch_field().resolve_over(Sampling.at_times([0.0, 1.0]))


def test_a_carrier_undefined_between_samples_stops_the_lift() -> None:
    """Opposed normals have no blend, so an instant only the cloud samples is Unresolvable."""
    poses = np.tile(np.eye(4), (2, 1, 1))
    poses[1, :3, :3] = np.diag([1.0, -1.0, -1.0])  # a half turn about x: the normal ends up opposed
    surface = FaceSignal.of(_patch(), TransformSignal.from_matrices([0.0, 2.0], poses))
    cloud = Point3BundleSignal.from_frames([0.0, 1.0, 2.0], np.zeros((3, 2, 3)))  # samples t=1 too
    decided = surface.clearance(cloud).decide()
    assert isinstance(decided, Unresolvable)


def test_an_occluded_member_is_absent_from_its_frame_and_from_the_fold() -> None:
    present = np.array([[True, True, True], [True, False, True]])
    cloud = Point3BundleSignal.from_frames(
        [0.0, 1.0],
        np.array([[[0, 0, 3.0], [0, 0, 5.0], [0, 0, 9.0]], [[0, 0, 4.0], [0, 0, 1.0], [0, 0, 8.0]]]),
        keys=["a", "b", "c"],
        present=present,
    )
    surface = FaceSignal.of(
        _patch(), TransformSignal.from_samples([0.0, 1.0], [RigidTransform.identity(), RigidTransform.identity()])
    )
    frames = surface.clearance(cloud).resolve().values
    assert set(frames[1].support()) == {"a", "c"}  # 'b' is occluded there
    assert frames[1].roster == ("a", "b", "c")  # the roster still declares it
    folded = surface.clearance(cloud).min().resolve_over(Sampling.at_times([0.0, 1.0]))
    assert np.array_equal(folded, np.array([3.0, 4.0]))  # 1.0 is occluded, so it does not win


def test_a_frame_with_no_present_member_leaves_the_fold_undefined() -> None:
    cloud = Point3BundleSignal.from_frames(
        [0.0, 1.0],
        np.zeros((2, 2, 3)),
        keys=["a", "b"],
        present=np.array([[True, True], [False, False]]),
    )
    surface = FaceSignal.of(
        _patch(), TransformSignal.from_samples([0.0, 1.0], [RigidTransform.identity(), RigidTransform.identity()])
    )
    field = surface.clearance(cloud)
    assert isinstance(field.resolve().values[1].support(), tuple)
    decided = field.min().decide()
    assert isinstance(decided, Unresolvable)
    assert "empty frame" in decided.reason


def test_signals_that_never_overlap_do_not_lift() -> None:
    surface = FaceSignal.of(
        _patch(), TransformSignal.from_samples([0.0, 1.0], [RigidTransform.identity(), RigidTransform.identity()])
    )
    elsewhere = Point3BundleSignal.from_frames([5.0, 6.0], np.zeros((2, 2, 3)))
    decided = surface.clearance(elsewhere).decide()
    assert isinstance(decided, Unresolvable)
    assert "do not overlap" in decided.reason


def test_a_cloud_authored_in_a_non_world_frame_is_anchored_on_every_path() -> None:
    """The batched grid must world-anchor the stack, exactly as the per-point path does.

    A cloud may be authored in a non-world ``frame`` and its samples are world-anchored at build.
    Reading the *stored* coordinates back hands out frame-local positions under a world-anchored
    contract — the clearance to a patch 5 units below then reads 0.0 instead of 5.0. Every path
    through the cloud (decided members, dense readback, and a clearance lifted over it) has to
    agree with `Point3.at(..., frame=…)`.
    """
    from fungeom.primitives.frame.value import WORLD_FRAME

    rig = WORLD_FRAME.child("rig", RigidTransform.from_translation([0.0, 0.0, 5.0]))
    local = np.array([[[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]]] * 2)
    stamps = [0.0, 1.0]

    def cloud() -> Point3BundleSignal:
        return Point3BundleSignal.from_frames(stamps, local, keys=["a", "b"], frame=rig)

    expected = np.array([[Point3.at(*local[t, n], frame=rig).resolve().coord for n in range(2)] for t in range(2)])
    decided = np.array([[frame.members[k].coord for k in ("a", "b")] for frame in cloud().resolve().values])
    grid, _ = cloud().resolve_over(Sampling.at_times(stamps))
    assert np.array_equal(decided, expected)
    assert np.array_equal(grid, expected)  # the dense readback anchors too

    patch = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.rectangle(4, 4))
    pose = TransformSignal.from_matrices(stamps, np.tile(np.eye(4), (2, 1, 1)))

    def field() -> Any:
        return FaceSignal.of(patch, pose).clearance(cloud())

    lifted = np.array([[frame.members[k] for k in ("a", "b")] for frame in field().resolve().values])
    assert np.array_equal(lifted, np.full((2, 2), 5.0))  # 5 above the patch, not 0 on it
    assert np.array_equal(field().resolve_over(Sampling.at_times(stamps))[0], lifted)


def test_an_ungrounded_frame_defers_to_the_per_instant_path() -> None:
    """No world anchor means no world coordinates — the shortcut declines rather than inventing them.

    The generic path owns the subtlety: an ungrounded frame only bites once some point is actually
    built, so a stack with nothing present still resolves (to empty clouds).
    """
    from fungeom.primitives.frame.value import CoordinateFrame

    loose = CoordinateFrame.detached("loose")
    stamps = [0.0, 1.0]
    positions = np.array([[[1.0, 0.0, 0.0]], [[2.0, 0.0, 0.0]]])

    occupied = Point3BundleSignal.from_frames(stamps, positions, keys=["a"], frame=loose)
    assert isinstance(occupied.decide(), Unresolvable)
    with pytest.raises(UnresolvableError):
        occupied.resolve_over(Sampling.at_times(stamps))

    nothing_present = Point3BundleSignal.from_frames(
        stamps, positions, keys=["a"], frame=loose, present=np.array([[False], [False]])
    )
    _, mask = nothing_present.resolve_over(Sampling.at_times(stamps))
    assert not mask.any()  # resolvable, and empty — as it is point by point


# --- the cloud's index: cheap where it can be, honest where it cannot ------------------------------


def _still_patch(stamps: Any) -> FaceSignal:
    patch = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.rectangle(4, 4))
    poses = np.tile(np.eye(4), (len(stamps), 1, 1))
    return FaceSignal.of(patch, TransformSignal.from_matrices(stamps, poses))


def test_a_cloud_that_cannot_answer_its_index_cheaply_falls_back_to_deciding() -> None:
    """A derived cloud has no stored time base, so the default index decides — and still agrees."""
    stamps = [0.0, 1.0]
    positions = np.array([[[1.0, 0.0, 3.0], [0.0, 2.0, 7.0]]] * 2)
    lift = TransformSignal.from_matrices(stamps, np.tile(np.eye(4), (2, 1, 1)))

    def derived() -> Point3BundleSignal:  # a _Transformed… node, not the dense carrier
        return Point3BundleSignal.from_frames(stamps, positions, keys=["a", "b"]).transformed_by(lift)

    assert not isinstance(derived(), type(Point3BundleSignal.from_frames(stamps, positions)))
    field = _still_patch(stamps).clearance(derived())
    lifted = np.array([[frame.members[k] for k in ("a", "b")] for frame in field.resolve().values])
    assert np.array_equal(lifted, np.array([[3.0, 7.0]] * 2))


def test_an_unresolvable_cloud_stops_the_batched_lift() -> None:
    """The index propagates the cloud's own partiality when deciding is what it takes to know it."""
    from fungeom import Interval

    stamps = [0.0, 1.0]
    positions = np.array([[[1.0, 0.0, 3.0]]] * 2)
    stranded = Point3BundleSignal.from_frames(stamps, positions, keys=["a"]).restrict(Interval.of(9.0, 10.0))
    decided = _still_patch(stamps).clearance(stranded).decide()
    assert isinstance(decided, Unresolvable)


def test_a_cloud_whose_time_base_is_unresolvable_stops_the_batched_lift() -> None:
    """Even the cheap index has to decide the sampling — a non-increasing one has no time base."""
    backwards = Point3BundleSignal.from_frames([1.0, 0.0], np.array([[[1.0, 0.0, 3.0]]] * 2), keys=["a"])
    decided = _still_patch([0.0, 1.0]).clearance(backwards).decide()
    assert isinstance(decided, Unresolvable)


def test_a_cloud_with_the_wrong_number_of_frames_has_no_coherent_index() -> None:
    """A frame stack that does not line up with its time base is not a sampled field at all."""
    mismatched = Point3BundleSignal.from_frames(
        [0.0, 1.0, 2.0], np.array([[[1.0, 0.0, 3.0]]] * 2), keys=["a"]
    )  # 2 frames for 3 instants
    assert isinstance(mismatched._sample_index(), Unresolvable)
    decided = _still_patch([0.0, 1.0, 2.0]).clearance(mismatched).decide()
    assert isinstance(decided, Unresolvable)
    assert decided.reason == mismatched.decide().reason


def test_an_ungrounded_frame_surfaces_from_the_grid_rather_than_the_index() -> None:
    """The dense index is not a proof of resolvability; the values are where this one shows up."""
    from fungeom.primitives.frame.value import CoordinateFrame

    stamps = [0.0, 1.0]
    loose = Point3BundleSignal.from_frames(
        stamps, np.array([[[1.0, 0.0, 3.0]]] * 2), keys=["a"], frame=CoordinateFrame.detached("loose")
    )
    assert isinstance(loose._sample_index(), Resolvable)  # the index is answerable...
    decided = _still_patch(stamps).clearance(loose).decide()
    assert isinstance(decided, Unresolvable)  # ...but the lift is not
    assert decided.reason == loose.decide().reason  # and it reports what the per-instant path would


def test_a_hulled_patch_still_measures_without_a_static_face_to_batch_against() -> None:
    """The re-hulled (deforming) patch has no fixed footprint; it batches per frame all the same."""
    ring = np.array([[-1.0, -1.0, 0.0], [1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [-1.0, 1.0, 0.0]])
    hull_cloud = Point3BundleSignal.from_frames(_TIMES, np.tile(ring, (_FRAMES, 1, 1)))
    surface = hull_cloud.fit_convex_face(tolerance=1e-9)
    field = surface.clearance(Point3BundleSignal.from_frames(_TIMES, _CLOUD))
    values, _ = field.resolve_over(Sampling.at_times(_TIMES))
    assert np.array_equal(values, _decided_grid(field))
