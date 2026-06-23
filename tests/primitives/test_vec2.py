"""Vec2 — the planar vector, mirroring Vec3 (plus the scalar 2D cross)."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Scalar, Unresolvable, Vec2


def test_of_dispatches_and_resolves() -> None:
    assert np.allclose(Vec2.of(3, 4).resolve(), [3, 4])
    assert type(Vec2.of(1, 2)).__name__ == "LiteralVec2"
    v = Vec2.of(Vec2.of(3, 4).norm(), Scalar.of(1.0))
    assert type(v).__name__ == "ComponentVec2"
    assert np.allclose(v.resolve(), [5, 1])


def test_add_sub_scale_lerp() -> None:
    assert np.allclose((Vec2.of(1, 2) + Vec2.of(3, 4)).resolve(), [4, 6])
    assert np.allclose((Vec2.of(3, 4) - Vec2.of(1, 1)).resolve(), [2, 3])
    assert np.allclose(Vec2.of(3, 4).scale(2.0).resolve(), [6, 8])
    assert np.allclose(Vec2.of(0, 0).lerp(Vec2.of(10, 0), 0.5).resolve(), [5, 0])


def test_norm_dot_cross_normalized() -> None:
    assert Vec2.of(3, 4).norm().resolve() == 5.0
    assert Vec2.of(1, 2).dot(Vec2.of(3, 4)).resolve() == 11.0
    assert Vec2.of(1, 0).cross(Vec2.of(0, 1)).resolve() == 1.0  # signed area
    assert np.allclose(Vec2.of(3, 4).normalized().resolve(), [0.6, 0.8])


def test_project_reject_and_partialities() -> None:
    p, q = Vec2.of(2, 2), Vec2.of(1, 0)
    assert np.allclose(p.project_onto(q).resolve(), [2, 0])
    assert np.allclose(p.reject_from(q).resolve(), [0, 2])
    assert isinstance(Vec2.of(0, 0).normalized().decide(), Unresolvable)
    assert isinstance(p.project_onto(Vec2.of(0, 0)).decide(), Unresolvable)
    assert isinstance(p.reject_from(Vec2.of(0, 0)).decide(), Unresolvable)


def test_components_angle_perpendicular_with_norm() -> None:
    v = Vec2.of(3, 4)
    assert v.x().resolve() == 3.0
    assert v.y().resolve() == 4.0
    assert np.isclose(Vec2.of(1, 0).angle_to(Vec2.of(0, 1)).resolve(), np.pi / 2)
    assert np.allclose(Vec2.of(3, 0).perpendicular().resolve(), [0, 3])
    assert np.allclose(Vec2.of(0, 3).with_norm(10).resolve(), [0, 10])
    assert isinstance(Vec2.of(0, 0).angle_to(Vec2.of(1, 0)).decide(), Unresolvable)
    assert isinstance(Vec2.of(0, 0).with_norm(5).decide(), Unresolvable)


def test_value_rejects_wrong_shape() -> None:
    from fungeom.values import Float2  # noqa: F401  (documents the runtime value type)
    from fungeom.primitives.vec2.value import as_vec2

    assert np.allclose(as_vec2([1, 2]), [1, 2])
    with pytest.raises(ValueError):
        as_vec2([1, 2, 3])  # not 2-dimensional
