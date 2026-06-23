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
