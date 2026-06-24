"""Direction2 — a unit 2D direction and its algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction2, Scalar, Unresolvable, Vec2
from fungeom.values import Direction2Value


def test_constructors() -> None:
    assert np.allclose(Direction2.of(3, 4).resolve().vector, [0.6, 0.8])  # normalized
    assert np.allclose(Direction2.from_angle(np.pi / 2).resolve().vector, [0, 1], atol=1e-9)
    assert np.allclose(Direction2.towards(Vec2.of(2, 0)).resolve().vector, [1, 0])
    # a deferred component yields a graph that still normalizes
    assert np.allclose(Direction2.of(Scalar.of(3), 4).resolve().vector, [0.6, 0.8])


def test_zero_is_unresolvable() -> None:
    assert isinstance(Direction2.of(0, 0).decide(), Unresolvable)
    decision = Direction2.towards(Vec2.of(0, 0)).decide()
    assert isinstance(decision, Unresolvable)
    assert "zero vector" in decision.reason


def test_combinators() -> None:
    east = Direction2.of(1, 0)
    north = Direction2.of(0, 1)
    assert np.allclose(east.reversed().resolve().vector, [-1, 0])
    assert np.allclose(east.perpendicular().resolve().vector, [0, 1])  # quarter turn CCW
    assert east.dot(north).resolve() == 0.0
    assert np.isclose(east.angle_to(north).resolve(), np.pi / 2)
    assert np.isclose(north.angle().resolve(), np.pi / 2)  # oriented angle from +x
    assert np.allclose(east.as_vector().resolve(), [1, 0])


def test_value_helpers() -> None:
    value = Direction2Value.of(1, 0)
    assert value.approx_equal(Direction2Value.of(2, 0))  # normalized, so equal
    assert not value.approx_equal(value.reversed())
    assert np.isclose(value.angle(), 0.0)
    assert repr(value) == "Direction2Value([1, 0])"


def test_zero_vector_value_is_rejected() -> None:
    # the value type enforces the unit invariant (the facade short-circuits before this)
    with pytest.raises(ValueError, match="zero vector"):
        Direction2Value(vector=np.zeros(2))
