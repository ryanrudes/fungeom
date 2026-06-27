"""FaceSignal — a moving patch: a static Face transported by a pose signal over time."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    Direction3,
    Face,
    FaceSignal,
    Instant,
    Interval,
    Plane,
    Point3,
    Point3Bundle,
    Point3BundleSignal,
    Point3Signal,
    RigidTransform,
    Region2,
    Sampling,
    TransformSignal,
    Unresolvable,
    UnresolvableError,
)


def _rising_patch() -> FaceSignal:
    # a 4x2 rectangle on the z=0 plane, fixed in a frame that rises z: 0 -> 2 over [0, 2]
    patch = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.rectangle(4, 2))
    pose = TransformSignal.from_samples(
        [0.0, 2.0], [RigidTransform.identity(), RigidTransform.from_translation([0, 0, 2])]
    )
    return FaceSignal.of(patch, pose)


def _grid() -> Sampling:
    return Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 3)  # t = 0, 1, 2


def test_plane_normal_origin_and_frame_over_time() -> None:
    patch = _rising_patch()
    assert np.allclose(patch.plane().origin().resolve_over(_grid())[:, 2], [0, 1, 2])  # rises in z
    assert np.allclose(patch.plane().normal().resolve_over(_grid()), [[0, 0, 1]] * 3)  # normal kept
    assert np.allclose(patch.frame().resolve_over(_grid())[:, 2, 3], [0, 1, 2])  # frame translation rises
    assert np.allclose(patch.frame().at(1.0).resolve().rotation[:, 2], [0, 0, 1])  # +z col = normal
    assert patch.at(1.0).clearance(Point3.at(0, 0, 1)).resolve() == 0.0  # the transported patch is a Face


def test_boundary_is_the_moving_footprint() -> None:
    patch = _rising_patch()
    values, mask = patch.boundary().resolve_over(_grid())
    assert values.shape == (3, 4, 3)  # 3 frames, 4 corners, 3D
    assert mask.all()
    assert np.allclose(values[:, :, 2].T, [[0, 1, 2]] * 4)  # every corner rises with the patch


def test_clearance_point_and_cloud() -> None:
    patch = _rising_patch()
    foot = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])  # fixed 5 up
    assert np.allclose(patch.clearance(foot).resolve_over(_grid()), [5, 4, 3])  # shrinks as the patch rises
    cloud = Point3BundleSignal.from_frames(
        [0.0, 2.0], [[[0, 0, 5], [0.5, 0, 5]], [[0, 0, 5], [0.5, 0, 5]]], keys=["a", "b"]
    )
    values, mask = patch.clearance(cloud).resolve_over(_grid())  # ScalarBundleSignal -> (T, K)
    assert np.allclose(values, [[5, 5], [4, 4], [3, 3]])


def test_contains_footprint_membership_over_time() -> None:
    patch = _rising_patch()
    over = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])  # projects inside the footprint
    beside = Point3Signal.from_samples([0.0, 2.0], [[10, 0, 5], [10, 0, 5]])  # outside it
    assert patch.contains(over).at(1.0).resolve() is True
    assert patch.contains(beside).at(1.0).resolve() is False


def test_partiality_flows_from_pose_point_and_region() -> None:
    patch = _rising_patch()
    # a query off the pose's support -> Unresolvable, not an invented number
    foot = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])
    assert isinstance(patch.clearance(foot).at(9.0).decide(), Unresolvable)
    # an empty patch has no frame
    empty = FaceSignal.of(
        Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty),
        TransformSignal.from_samples([0.0, 2.0], [RigidTransform.identity(), RigidTransform.identity()]),
    )
    assert isinstance(empty.frame().decide(), Unresolvable)


def test_at_off_support_is_unresolvable() -> None:
    patch = _rising_patch()  # pose support is [0, 2]
    assert isinstance(patch.at(9.0).decide(), Unresolvable)  # the transported patch is undefined off-support


def test_blend_across_a_flipped_patch_is_unresolvable() -> None:
    from scipy.spatial.transform import Rotation

    # a pose that flips the patch normal (+z -> -z) between samples: the mid-sample patch blend is
    # antipodal (no unique orientation), so sampling the moving patch there is Unresolvable
    patch = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.rectangle(2, 2))
    flip = TransformSignal.from_samples(
        [0.0, 2.0],
        [RigidTransform.identity(), RigidTransform.from_rotation(Rotation.from_euler("x", 180, degrees=True))],
    )
    moving = FaceSignal.of(patch, flip)
    assert isinstance(moving.at(1.0).decide(), Unresolvable)  # FACE_BLEND over opposed normals


def test_boundary_and_frame_transport_rotation_in_both_paths() -> None:
    # the fix: a rotating pose must rotate the footprint vertices (R·v + t), not just translate to
    # the moved centroid — and the vectorized readback must agree with the per-instant (_decide) path.
    pts = Point3Bundle.from_map({"a": Point3.at(0, 0, 0), "b": Point3.at(1, 0, 0), "c": Point3.at(0, 1, 0)})
    face = Face.on(pts.fit_plane(), Region2.hull(pts.in_frame(pts.fit_plane())))
    rot = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
    trans = np.array([1.0, 2.0, 3.0])
    m = np.eye(4)
    m[:3, :3] = rot
    m[:3, 3] = trans
    fs = FaceSignal.of(face, TransformSignal.from_matrices(np.array([0.0]), m[None]))
    grid = Sampling.at_times([0.0])

    static_verts = np.array([face.boundary().at(k).resolve().coord for k in range(3)])
    got = fs.boundary().resolve_over(grid)[0][0]  # (K, 3)
    assert np.allclose(np.sort(got, axis=0), np.sort(static_verts @ rot.T + trans, axis=0))  # R·v + t
    # the _decide path (via at) reproduces the vectorized readback
    at_cloud = fs.boundary().at(0.0).resolve()
    assert np.allclose([at_cloud.members[k].coord for k in at_cloud.roster], got)

    # frame transports rigidly: rotation = R · static_frame.R, origin = R · static_origin + t
    static_frame = face.frame().resolve()
    frame = fs.frame().resolve_over(grid)[0]
    assert np.allclose(frame[:3, :3], rot @ static_frame.rotation)
    assert np.allclose(frame[:3, 3], rot @ static_frame.translation + trans)
    assert np.allclose(fs.frame().at(0.0).resolve().matrix, frame)  # _decide path matches


def test_clearance_and_plane_readbacks_match_per_instant_under_rotation() -> None:
    # the vectorized resolve_over of clearance / signed_distance / normal / origin must agree with
    # the per-instant .at() path at the sample instants — including a rotation about the normal,
    # which the footprint must follow (the transformed_by fix; resolve_over inverse-transports it).
    from scipy.spatial.transform import Rotation

    pts = Point3Bundle.from_map(
        {k: Point3.at(*v) for k, v in {"a": (-1, -1, 0), "b": (1, -1, 0), "c": (1, 1, 0), "d": (-1, 1, 0)}.items()}
    )
    face = Face.on(pts.fit_plane().facing(Point3.at(0, 0, 1.0)), Region2.hull(pts.in_frame(pts.fit_plane())))
    m0, m1 = np.eye(4), np.eye(4)
    m1[:3, :3] = Rotation.from_euler("z", 90, degrees=True).as_matrix()  # a 90° spin about the normal
    m1[0, 3] = 1.5  # plus a translation, between the two samples
    fs = FaceSignal.of(face, TransformSignal.from_matrices(np.array([0.0, 1.0]), np.array([m0, m1])))
    grid = Sampling.at_times([0.0, 1.0])
    cloud = Point3BundleSignal.from_frames([0.0, 1.0], [[[1.3, 0.0, 0.4], [0.0, 0.0, 0.2]]] * 2, keys=["edge", "mid"])
    point = Point3Signal.from_samples([0.0, 1.0], [[1.3, 0.0, 0.4]] * 2)

    clear_cloud, mask = fs.clearance(cloud).resolve_over(grid)
    clear_point = fs.clearance(point).resolve_over(grid)
    sd_cloud, _ = fs.plane().signed_distance(cloud).resolve_over(grid)
    sd_point = fs.plane().signed_distance(point).resolve_over(grid)
    normals = fs.plane().normal().resolve_over(grid)
    origins = fs.plane().origin().resolve_over(grid)
    assert mask.all()

    for i, t in enumerate([0.0, 1.0]):
        bundle = fs.clearance(cloud).at(t).resolve()
        assert np.allclose([bundle.members[k] for k in bundle.roster], clear_cloud[i])
        assert np.isclose(fs.clearance(point).at(t).resolve(), clear_point[i])
        sd = fs.plane().signed_distance(cloud).at(t).resolve()
        assert np.allclose([sd.members[k] for k in sd.roster], sd_cloud[i])
        assert np.isclose(fs.plane().signed_distance(point).at(t).resolve(), sd_point[i])
        assert np.allclose(fs.plane().normal().at(t).resolve().vector, normals[i])
        assert np.allclose(fs.plane().origin().at(t).resolve().coord, origins[i])

    # the spin genuinely moved the footprint: the 'edge' marker reads a different bounded clearance
    # at the rotated instant than at the identity one (resolve_over isn't dropping the rotation).
    assert not np.isclose(clear_cloud[0, 0], clear_cloud[1, 0])


def test_clearance_resolve_over_masks_occluded_cloud_members() -> None:
    patch = _rising_patch()  # pose rises z: 0 → 2 over [0, 2]
    cloud = Point3BundleSignal.from_frames(
        [0.0, 2.0],
        [[[0, 0, 5], [0.5, 0, 5]], [[0, 0, 5], [0.5, 0, 5]]],
        keys=["a", "b"],
        present=[[True, True], [True, False]],  # 'b' occluded at t = 2
    )
    values, mask = patch.clearance(cloud).resolve_over(Sampling.at_times([0.0, 2.0]))
    assert mask.tolist() == [[True, True], [True, False]]
    assert np.isnan(values[1, 1])  # the occluded cell is nan with a False mask, like resolved_grid
    assert np.allclose([values[0, 0], values[0, 1], values[1, 0]], [5, 5, 3])  # present cells resolve


def test_clearance_resolve_over_on_an_empty_face_raises() -> None:
    empty = FaceSignal.of(
        Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty),
        TransformSignal.from_samples([0.0, 2.0], [RigidTransform.identity(), RigidTransform.identity()]),
    )
    grid = Sampling.at_times([0.0, 2.0])
    foot = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])
    cloud = Point3BundleSignal.from_frames([0.0, 2.0], [[[0, 0, 5]], [[0, 0, 5]]], keys=["m"])
    with pytest.raises(UnresolvableError):  # an empty patch has no surface to measure to
        empty.clearance(foot).resolve_over(grid)
    with pytest.raises(UnresolvableError):
        empty.clearance(cloud).resolve_over(grid)
