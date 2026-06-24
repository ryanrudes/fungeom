"""Line — an oriented line and its algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction3, Line, Point3, Unresolvable
from fungeom.values import LineValue


def _x_axis() -> Line:
    # the x-axis, directed +x
    return Line.through(Point3.at(0, 0, 0), Direction3.of(1, 0, 0))


def test_constructors() -> None:
    assert isinstance(_x_axis().resolve(), LineValue)
    through_points = Line.through_points(Point3.at(0, 0, 0), Point3.at(0, 4, 0))
    assert np.allclose(through_points.direction().resolve().vector, [0, 1, 0])  # directed a → b


def test_constructor_partiality() -> None:
    coincident = Line.through_points(Point3.at(1, 1, 1), Point3.at(1, 1, 1))
    assert "coincident" in coincident.decide().reason


def test_query() -> None:
    line = _x_axis()
    assert np.allclose(line.direction().resolve().vector, [1, 0, 0])
    assert np.allclose(line.origin().resolve().coord, [0, 0, 0])
    assert np.allclose(line.project(Point3.at(2, 5, 0)).resolve().coord, [2, 0, 0])  # foot drops onto the axis
    assert line.distance_to(Point3.at(2, 3, 4)).resolve() == 5.0  # √(3² + 4²)
    assert line.contains(Point3.at(7, 0, 0)).resolve() is True
    assert line.contains(Point3.at(7, 1, 0)).resolve() is False


def test_direction_along_orients_the_line() -> None:
    line = _x_axis()
    forward = [Point3.at(0, 1, 0), Point3.at(2, -1, 0), Point3.at(5, 3, 0)]  # increasing x (off the line is fine)
    assert np.allclose(line.direction_along(forward).resolve().vector, [1, 0, 0])
    assert np.allclose(line.direction_along(list(reversed(forward))).resolve().vector, [-1, 0, 0])


def test_direction_along_partiality() -> None:
    line = _x_axis()
    # a fold-back: parameters 0, 2, 1 are not monotone
    foldback = line.direction_along([Point3.at(0, 0, 0), Point3.at(2, 0, 0), Point3.at(1, 0, 0)])
    decision = foldback.decide()
    assert isinstance(decision, Unresolvable)
    assert "coherent monotone order" in decision.reason
    # a tie (two points with the same parameter) is not strictly monotone either
    tie = line.direction_along([Point3.at(0, 5, 0), Point3.at(0, -5, 0), Point3.at(3, 0, 0)])
    assert isinstance(tie.decide(), Unresolvable)
    # fewer than two points cannot orient anything
    too_few = line.direction_along([Point3.at(0, 0, 0)])
    assert "at least two" in too_few.decide().reason


def test_line_value_helpers() -> None:
    value = _x_axis().resolve()
    assert value.parameter(Point3.at(3, 9, 9).resolve().coord) == 3.0
    same = Line.through(Point3.at(8, 0, 0), Direction3.of(1, 0, 0)).resolve()  # same oriented line, shifted anchor
    assert value.approx_equal(same)
    assert not value.approx_equal(value.reversed())  # oriented: a reverse is a different line
    assert repr(value) == "LineValue(point=[0, 0, 0], direction=[1, 0, 0])"


def test_zero_direction_is_rejected() -> None:
    # the value type enforces the unit-direction invariant (the facade never hits this)
    with pytest.raises(ValueError, match="zero direction"):
        LineValue(point=np.zeros(3), direction=np.zeros(3))
