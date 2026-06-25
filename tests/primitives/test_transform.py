"""Transform — rigid transforms (SE(3)): construction, composition, value ops."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from fungeom import Direction3, RigidTransform, Scalar, Transform, Unresolvable, Vec3


def test_identity_known_translation() -> None:
    assert Transform.identity().resolve().approx_equal(RigidTransform.identity())
    assert np.allclose(Transform.known(RigidTransform.from_translation([5, 0, 0])).resolve().translation, [5, 0, 0])
    assert np.allclose(Transform.translation(Vec3.of(0, 3, 4)).resolve().translation, [0, 3, 4])
    assert np.allclose(Transform.translation([1, 2, 3]).resolve().translation, [1, 2, 3])  # raw components


def test_rotation_accepts_vector_or_direction_axis() -> None:
    a = Transform.rotation(Vec3.of(0, 0, 1), Scalar.of(np.pi / 2)).resolve()
    b = Transform.rotation(Direction3.of(0, 0, 1), Scalar.of(np.pi / 2)).resolve()
    assert np.allclose(a.apply_point([1, 0, 0]), [0, 1, 0], atol=1e-9)
    assert a.approx_equal(b)


def test_compose_inverse_slerp() -> None:
    t = Transform.translation(Vec3.of(1, 0, 0))
    assert np.allclose((t @ t).resolve().translation, [2, 0, 0])
    assert np.allclose(t.inverse().resolve().translation, [-1, 0, 0])
    half = Transform.identity().slerp(Transform.translation(Vec3.of(10, 0, 0)), 0.5)
    assert np.allclose(half.resolve().translation, [5, 0, 0])


def test_apply_and_decompose() -> None:
    spin = Transform.rotation(Vec3.of(0, 0, 1), Scalar.of(np.pi / 2))
    # a free vector is rotated only (no translation)
    assert np.allclose(spin.transform_vector(Vec3.of(1, 0, 0)).resolve(), [0, 1, 0], atol=1e-9)
    assert np.allclose(spin.transform_direction(Direction3.of(1, 0, 0)).resolve().vector, [0, 1, 0], atol=1e-9)
    moved = spin @ Transform.translation(Vec3.of(3, 0, 0))
    assert np.allclose(moved.translation_part().resolve(), [0, 3, 0], atol=1e-9)  # R·t
    # rotation_part strips translation but keeps the rotation
    rot_only = moved.rotation_part().resolve()
    assert np.allclose(rot_only.translation, [0, 0, 0], atol=1e-9)
    assert np.allclose(rot_only.apply_point([1, 0, 0]), [0, 1, 0], atol=1e-9)


def test_aligning_is_the_shortest_arc_rotation() -> None:
    t = Transform.aligning(Direction3.of(1, 0, 0), Direction3.of(0, 1, 0))
    assert np.allclose(t.transform_direction(Direction3.of(1, 0, 0)).resolve().vector, [0, 1, 0], atol=1e-9)
    # already aligned → identity; antipodal → no unique shortest arc
    same = Transform.aligning(Direction3.of(0, 0, 1), Direction3.of(0, 0, 1))
    assert same.resolve().approx_equal(RigidTransform.identity())
    anti = Transform.aligning(Direction3.of(1, 0, 0), Direction3.of(-1, 0, 0)).decide()
    assert isinstance(anti, Unresolvable)
    assert "antipodal" in anti.reason


def test_from_axes_builds_an_orthonormal_frame() -> None:
    # a non-perpendicular y hint is Gram-Schmidt-projected → still orthonormal & right-handed
    frame = Transform.from_axes(Direction3.of(1, 0, 0), Direction3.of(1, 1, 0), origin=(5, 0, 0))
    value = frame.resolve()
    assert np.allclose(value.rotation[:, 0], [1, 0, 0])  # +x is exact
    assert np.allclose(value.rotation[:, 2], [0, 0, 1])  # +z = x × y
    assert np.allclose(value.rotation.T @ value.rotation, np.eye(3))
    assert np.isclose(np.linalg.det(value.rotation), 1.0)  # right-handed
    assert np.allclose(value.translation, [5, 0, 0])
    parallel = Transform.from_axes(Direction3.of(1, 0, 0), Direction3.of(1, 0, 0)).decide()
    assert isinstance(parallel, Unresolvable)
    assert "parallel" in parallel.reason


def test_look_at_views_toward_the_target() -> None:
    frame = Transform.look_at(eye=(0, 0, 0), target=(0, 0, 5), up=Direction3.of(0, 1, 0))
    value = frame.resolve()
    assert np.allclose(value.rotation[:, 2], [0, 0, 1])  # +z = forward (toward target)
    assert np.allclose(value.translation, [0, 0, 0])  # placed at the eye
    assert np.allclose(value.rotation.T @ value.rotation, np.eye(3))
    coincident = Transform.look_at((1, 1, 1), (1, 1, 1), up=Direction3.of(0, 1, 0)).decide()
    assert isinstance(coincident, Unresolvable)
    assert "coincide" in coincident.reason
    aligned_up = Transform.look_at((0, 0, 0), (0, 0, 5), up=Direction3.of(0, 0, 1)).decide()
    assert isinstance(aligned_up, Unresolvable)
    assert "parallel to the view direction" in aligned_up.reason


def test_static_geometry_constructors_propagate(bad: object) -> None:
    bad_d = bad.direction3  # type: ignore[attr-defined]
    good_d = Direction3.of(1, 0, 0)
    assert isinstance(Transform.aligning(bad_d, good_d).decide(), Unresolvable)
    assert isinstance(Transform.aligning(good_d, bad_d).decide(), Unresolvable)
    assert isinstance(Transform.from_axes(bad_d, good_d).decide(), Unresolvable)
    assert isinstance(Transform.from_axes(good_d, bad_d).decide(), Unresolvable)
    assert isinstance(
        Transform.from_axes(Direction3.of(1, 0, 0), Direction3.of(0, 1, 0), origin=bad.vec3).decide(), Unresolvable
    )  # type: ignore[attr-defined]
    assert isinstance(Transform.look_at(bad.vec3, (0, 0, 1), up=good_d).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(Transform.look_at((0, 0, 0), bad.vec3, up=good_d).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(Transform.look_at((0, 0, 0), (0, 0, 1), up=bad_d).decide(), Unresolvable)


def test_partialities_and_propagation(bad: object) -> None:
    assert isinstance(Transform.rotation(Vec3.of(0, 0, 0), Scalar.of(1)).decide(), Unresolvable)  # zero axis
    bad_scalar = bad.scalar  # type: ignore[attr-defined]
    assert isinstance(Transform.rotation(Vec3.of(0, 0, 1), bad_scalar).decide(), Unresolvable)  # bad angle
    assert isinstance(Transform.translation(bad.vec3).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(Transform.identity().slerp(Transform.identity(), bad_scalar).decide(), Unresolvable)


def test_rigid_transform_value_methods() -> None:
    rot = RigidTransform.from_rotation(Rotation.from_euler("z", 90, degrees=True), [1, 0, 0])
    assert np.allclose(rot.apply_vector([1, 0, 0]), [0, 1, 0], atol=1e-9)  # rotated, not translated
    assert np.allclose(rot.apply_point([1, 0, 0]), [1, 1, 0], atol=1e-9)  # rotated + translated
    assert rot.approx_equal(RigidTransform.from_matrix(rot.matrix))
    assert not rot.approx_equal(RigidTransform.identity())
    assert "rotation_xyz" in repr(rot) and "translation" in repr(RigidTransform.identity())
    with pytest.raises(ValueError):
        RigidTransform(np.eye(3))  # type: ignore[arg-type]  # not 4x4
