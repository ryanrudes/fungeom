"""Direction3 — a unit vector enforced by its value type."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction3, Unresolvable, Vec3


def test_of_and_towards_normalize() -> None:
    assert np.allclose(Direction3.of(0, 0, 5).resolve().vector, [0, 0, 1])
    assert np.allclose(Direction3.towards(Vec3.of(3, 4, 0)).resolve().vector, [0.6, 0.8, 0])
    # deferred components route through the graph
    assert np.allclose(Direction3.of(Vec3.of(3, 4, 0).norm(), 0, 0).resolve().vector, [1, 0, 0])


def test_zero_is_unresolvable_not_a_raise() -> None:
    assert isinstance(Direction3.of(0, 0, 0).decide(), Unresolvable)  # literal
    assert isinstance(Direction3.towards(Vec3.of(0, 0, 0)).decide(), Unresolvable)  # deferred


def test_reversed_angle_slerp_as_vector() -> None:
    x, y = Direction3.of(1, 0, 0), Direction3.of(0, 1, 0)
    assert np.allclose(x.reversed().resolve().vector, [-1, 0, 0])  # no -0.0
    assert x.angle_to(y).resolve() == pytest.approx(np.pi / 2)
    assert np.allclose(x.slerp(y, 0.5).resolve().vector, [np.sqrt(0.5), np.sqrt(0.5), 0])
    assert np.allclose(x.slerp(x, 0.5).resolve().vector, [1, 0, 0])  # parallel -> a
    assert np.allclose(x.as_vector().resolve(), [1, 0, 0])


def test_dot_and_cross() -> None:
    x, y = Direction3.of(1, 0, 0), Direction3.of(0, 1, 0)
    assert x.dot(y).resolve() == pytest.approx(0.0)
    assert x.dot(x).resolve() == pytest.approx(1.0)
    assert x.dot(x.reversed()).resolve() == pytest.approx(-1.0)
    assert np.allclose(x.cross(y).resolve().vector, [0, 0, 1])


def test_slerp_antipodal_is_unresolvable() -> None:
    assert isinstance(Direction3.of(1, 0, 0).slerp(Direction3.of(-1, 0, 0), 0.5).decide(), Unresolvable)


def test_cross_of_parallel_is_unresolvable() -> None:
    x = Direction3.of(1, 0, 0)
    assert isinstance(x.cross(x).decide(), Unresolvable)  # parallel
    assert isinstance(x.cross(x.reversed()).decide(), Unresolvable)  # antiparallel


def test_value_enforces_unit_length_eagerly() -> None:
    from fungeom.values import Direction3Value

    with pytest.raises(ValueError):
        Direction3Value.of(0, 0, 0)
    d = Direction3Value.of(0, 0, 2)
    assert np.allclose(d.vector, [0, 0, 1])
    assert d.approx_equal(Direction3Value.of(0, 0, 5))
    assert not d.approx_equal(Direction3Value.of(0, 2, 0))
    assert d.angle_to(Direction3Value.of(0, 0, 1)) == pytest.approx(0.0)
    assert "Direction3Value" in repr(d)
