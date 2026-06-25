"""Vec3 — construction (literal & deferred), algebra, and partialities."""

from __future__ import annotations

import numpy as np

from fungeom import Scalar, Unresolvable, Vec3


def test_of_dispatches_literal_vs_graph() -> None:
    assert np.allclose(Vec3.of(1, 2, 3).resolve(), [1, 2, 3])
    assert type(Vec3.of(1, 2, 3)).__name__ == "LiteralVec3"
    # a deferred component makes it a graph; bare numbers coerce alongside
    norm = Vec3.of(3, 4, 0).norm()  # a Scalar -> 5
    v = Vec3.of(norm, 0.0, Scalar.of(1.0))
    assert type(v).__name__ == "ComponentVec3"
    assert np.allclose(v.resolve(), [5, 0, 1])


def test_resolves_to_an_array() -> None:
    resolved = Vec3.of(1, 2, 3).resolve()
    assert isinstance(resolved, np.ndarray)


def test_add_sub_scale_negate() -> None:
    a, b = Vec3.of(1, 2, 3), Vec3.of(4, 0, -3)
    assert np.allclose((a + b).resolve(), [5, 2, 0])
    assert np.allclose((a - b).resolve(), [-3, 2, 6])
    assert np.allclose(a.scale(2.0).resolve(), [2, 4, 6])
    assert np.allclose(a.scale(Vec3.of(0, 3, 4).norm()).resolve(), [5, 10, 15])  # scale by a Scalar
    assert np.allclose(a.negate().resolve(), [-1, -2, -3])


def test_norm_dot_cross_lerp() -> None:
    assert Vec3.of(3, 4, 0).norm().resolve() == 5.0
    a, b = Vec3.of(1, 0, 0), Vec3.of(0, 1, 0)
    assert a.dot(b).resolve() == 0.0
    assert np.allclose(a.cross(b).resolve(), [0, 0, 1])
    assert np.allclose(a.lerp(b, 0.5).resolve(), [0.5, 0.5, 0])


def test_scalar_triple_is_the_signed_volume() -> None:
    # the standard basis spans a unit (right-handed) volume
    assert Vec3.of(1, 0, 0).scalar_triple(Vec3.of(0, 1, 0), Vec3.of(0, 0, 1)).resolve() == 1.0
    # swapping two vectors flips the sign
    assert Vec3.of(0, 1, 0).scalar_triple(Vec3.of(1, 0, 0), Vec3.of(0, 0, 1)).resolve() == -1.0
    # coplanar vectors enclose no volume
    assert Vec3.of(1, 0, 0).scalar_triple(Vec3.of(0, 1, 0), Vec3.of(1, 1, 0)).resolve() == 0.0


def test_normalized_project_reject_and_partialities() -> None:
    assert np.allclose(Vec3.of(0, 3, 4).normalized().resolve(), [0, 0.6, 0.8])
    a, b = Vec3.of(2, 2, 0), Vec3.of(1, 0, 0)
    assert np.allclose(a.project_onto(b).resolve(), [2, 0, 0])
    assert np.allclose(a.reject_from(b).resolve(), [0, 2, 0])
    assert isinstance(Vec3.of(0, 0, 0).normalized().decide(), Unresolvable)
    assert isinstance(a.project_onto(Vec3.of(0, 0, 0)).decide(), Unresolvable)
    assert isinstance(a.reject_from(Vec3.of(0, 0, 0)).decide(), Unresolvable)


def test_components_angle_and_with_norm() -> None:
    v = Vec3.of(3, 4, 12)
    assert v.x().resolve() == 3.0
    assert v.y().resolve() == 4.0
    assert v.z().resolve() == 12.0
    assert np.isclose(Vec3.of(1, 0, 0).angle_to(Vec3.of(0, 1, 0)).resolve(), np.pi / 2)
    assert np.isclose(Vec3.of(1, 0, 0).angle_to(Vec3.of(1, 0, 0)).resolve(), 0.0)
    assert np.allclose(Vec3.of(0, 3, 4).with_norm(10).resolve(), [0, 6, 8])
    # partialities: angle/length need a direction
    assert isinstance(Vec3.of(0, 0, 0).angle_to(Vec3.of(1, 0, 0)).decide(), Unresolvable)
    assert isinstance(Vec3.of(1, 0, 0).angle_to(Vec3.of(0, 0, 0)).decide(), Unresolvable)
    assert isinstance(Vec3.of(0, 0, 0).with_norm(5).decide(), Unresolvable)


def test_value_rejects_wrong_shape() -> None:
    import pytest

    from fungeom.primitives.vec3.value import as_vec3

    assert np.allclose(as_vec3([1, 2, 3]), [1, 2, 3])
    with pytest.raises(ValueError):
        as_vec3([1, 2])  # not 3-dimensional
