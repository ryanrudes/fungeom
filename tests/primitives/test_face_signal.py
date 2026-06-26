"""FaceSignal — a moving patch: a static Face transported by a pose signal over time."""

from __future__ import annotations

import numpy as np

from fungeom import (
    Direction3,
    Face,
    FaceSignal,
    Instant,
    Interval,
    Plane,
    Point3,
    Point3BundleSignal,
    Point3Signal,
    RigidTransform,
    Region2,
    Sampling,
    TransformSignal,
    Unresolvable,
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
