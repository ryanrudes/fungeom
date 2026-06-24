"""Transform2 — a rigid 2D transform (SE(2)) and its algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction2, RigidTransform2, Scalar, Transform2, Vec2


def test_constructors_and_apply() -> None:
    assert Transform2.identity().resolve().approx_equal(RigidTransform2.identity())
    quarter = Transform2.rotation(np.pi / 2)
    assert np.allclose(quarter.transform_vector(Vec2.of(1, 0)).resolve(), [0, 1], atol=1e-9)
    # a direction stays unit length under the rotation
    assert np.allclose(quarter.transform_direction(Direction2.of(1, 0)).resolve().vector, [0, 1], atol=1e-9)
    shift = Transform2.translation(Vec2.of(3, 4))
    assert np.allclose(shift.translation_part().resolve(), [3, 4])
    assert Transform2.known(RigidTransform2.from_angle(0.0)).resolve().approx_equal(RigidTransform2.identity())


def test_compose_inverse_and_decompose() -> None:
    shift = Transform2.translation(Vec2.of(1, 0))
    quarter = Transform2.rotation(np.pi / 2)
    # compose applies the right operand first: rotate (1,0)->(0,1), then translate +x -> (1,1)
    composed = (shift @ quarter).resolve()
    assert np.allclose(composed.apply_point(np.array([1.0, 0.0])), [1, 1], atol=1e-9)
    # inverse undoes
    assert (shift @ shift.inverse()).resolve().approx_equal(RigidTransform2.identity())
    # decompose: angle and rotation_part. Use a transform with BOTH rotation and translation
    # so the assertion is not vacuous — rotation_part must *keep* the rotation and *drop* the shift.
    assert np.isclose(quarter.angle().resolve(), np.pi / 2)
    both = shift @ quarter  # a quarter turn then a +x shift
    rotation_only = both.rotation_part().resolve()
    assert np.isclose(rotation_only.angle(), np.pi / 2)  # rotation preserved
    assert np.allclose(rotation_only.translation, [0, 0])  # translation dropped


def test_slerp_interpolates_rotation_and_translation() -> None:
    a = Transform2.identity()
    b = Transform2.translation(Vec2.of(4, 0)) @ Transform2.rotation(np.pi / 2)
    half = a.slerp(b, 0.5).resolve()
    assert np.isclose(half.angle(), np.pi / 4)  # rotation interpolated
    assert np.allclose(half.translation, [2, 0])  # translation lerped
    assert a.slerp(b, 0.0).resolve().approx_equal(a.resolve())  # endpoints
    assert a.slerp(b, 1.0).resolve().approx_equal(b.resolve())
    assert np.isclose(a.slerp(b, Scalar.of(0.5)).resolve().angle(), np.pi / 4)  # deferred t
    # the rotation takes the *shortest* arc: −10° to +10° passes through 0°, not 180°
    left = Transform2.rotation(np.radians(-10))
    right = Transform2.rotation(np.radians(10))
    assert np.isclose(left.slerp(right, 0.5).resolve().angle(), 0.0, atol=1e-9)


def test_deferred_resolvability_propagates() -> None:
    # a transform built from a deferred scalar/vector inherits resolvability
    assert Transform2.rotation(Scalar.of(0)).resolve().approx_equal(RigidTransform2.identity())
    bad = Transform2.rotation(Scalar.of(1) / Scalar.of(0))
    assert bad.decide().reason  # Unresolvable, reason intact


def test_value_helpers() -> None:
    value = RigidTransform2.from_angle(np.pi / 2, translation=np.array([1.0, 2.0]))
    assert np.allclose(value.translation, [1, 2])
    assert np.isclose(value.angle(), np.pi / 2)
    assert np.allclose(value.rotation, [[0, -1], [1, 0]], atol=1e-9)
    assert value.apply_vector(np.array([1.0, 0.0])).round(9).tolist() == [0, 1]  # rotation only
    assert "angle°=90" in repr(value)
    assert repr(RigidTransform2.identity()) == "RigidTransform2(translation=[0, 0])"
    # value-level compose via @
    shift = RigidTransform2.from_translation(np.array([2.0, 0.0]))
    assert np.allclose((value @ shift).apply_point(np.array([0.0, 0.0])), value.apply_point(np.array([2.0, 0.0])))


def test_wrong_shape_matrix_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be 3x3"):
        RigidTransform2(np.eye(4))  # type: ignore[arg-type]
