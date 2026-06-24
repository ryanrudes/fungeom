"""Line2 — an oriented 2D line (a planar hyperplane) and its algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction2, Line2, Point2, Unresolvable
from fungeom.values import Line2Value


def _x_axis() -> Line2:
    return Line2.through(Point2.at(0, 0), Direction2.of(1, 0))


def test_constructors_and_readers() -> None:
    assert isinstance(_x_axis().resolve(), Line2Value)
    through_points = Line2.through_points(Point2.at(0, 0), Point2.at(0, 4))
    assert np.allclose(through_points.direction().resolve().vector, [0, 1])  # directed a → b
    assert np.allclose(_x_axis().normal().resolve().vector, [0, 1])  # left normal of +x is +y
    assert np.allclose(_x_axis().origin().resolve().coord, [0, 0])


def test_plane_like_signed_distance_and_projection() -> None:
    line = _x_axis()
    assert line.signed_distance(Point2.at(0, 3)).resolve() == 3.0  # left of +x → positive
    assert line.signed_distance(Point2.at(0, -3)).resolve() == -3.0  # right → negative
    assert line.distance_to(Point2.at(5, -4)).resolve() == 4.0  # unsigned
    assert np.allclose(line.project(Point2.at(5, 9)).resolve().coord, [5, 0])
    assert line.contains(Point2.at(7, 0)).resolve() is True
    assert line.contains(Point2.at(7, 1)).resolve() is False


def test_constructor_partiality() -> None:
    coincident = Line2.through_points(Point2.at(1, 1), Point2.at(1, 1))
    assert isinstance(coincident.decide(), Unresolvable)
    assert "coincident" in coincident.decide().reason


def test_value_helpers() -> None:
    value = _x_axis().resolve()
    assert np.allclose(value.normal(), [0, 1])
    same = Line2.through(Point2.at(8, 0), Direction2.of(1, 0)).resolve()  # same oriented line, shifted anchor
    assert value.approx_equal(same)
    assert not value.approx_equal(value.reversed())  # oriented: a reverse flips the normal
    assert repr(value) == "Line2Value(point=[0, 0], direction=[1, 0])"


def test_zero_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero direction"):
        Line2Value(point=np.zeros(2), direction=np.zeros(2))
