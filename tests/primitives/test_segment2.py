"""Segment2 — a finite 2D line segment and its algebra."""

from __future__ import annotations

import numpy as np

from fungeom import Point2, Segment2, Unresolvable
from fungeom.values import Segment2Value


def _bone() -> Segment2:
    return Segment2.between(Point2.at(0, 0), Point2.at(4, 0))


def test_shape_and_endpoints() -> None:
    bone = _bone()
    assert isinstance(bone.resolve(), Segment2Value)
    assert bone.length().resolve() == 4.0
    assert np.allclose(bone.midpoint().resolve().coord, [2, 0])
    assert np.allclose(bone.direction().resolve().vector, [1, 0])
    assert np.allclose(bone.start().resolve().coord, [0, 0])
    assert np.allclose(bone.end().resolve().coord, [4, 0])


def test_query_clamps_to_the_endpoints() -> None:
    bone = _bone()
    assert np.allclose(bone.project(Point2.at(1, 5)).resolve().coord, [1, 0])  # interior
    assert np.allclose(bone.project(Point2.at(9, 5)).resolve().coord, [4, 0])  # past end
    assert np.allclose(bone.project(Point2.at(-9, 5)).resolve().coord, [0, 0])  # before start
    assert bone.distance_to(Point2.at(9, 3)).resolve() == np.hypot(5.0, 3.0)  # to the end
    assert bone.contains(Point2.at(2, 0)).resolve() is True
    assert bone.contains(Point2.at(9, 0)).resolve() is False  # on the line, past the end


def test_at_parameter_of_and_reversed() -> None:
    bone = _bone()
    assert np.allclose(bone.at(0.25).resolve().coord, [1, 0])
    assert bone.parameter_of(Point2.at(3, 0)).resolve() == 0.75
    assert bone.parameter_of(Point2.at(9, 0)).resolve() == 1.0  # clamped
    assert isinstance(bone.at(1.5).decide(), Unresolvable)
    assert np.allclose(bone.reversed().start().resolve().coord, [4, 0])
    assert np.allclose(bone.reversed().direction().resolve().vector, [-1, 0])


def test_degenerate_segment() -> None:
    point = Segment2.between(Point2.at(2, 2), Point2.at(2, 2))
    assert point.length().resolve() == 0.0
    assert isinstance(point.direction().decide(), Unresolvable)
    assert np.allclose(point.project(Point2.at(5, 5)).resolve().coord, [2, 2])  # collapses to the point
    assert point.parameter_of(Point2.at(5, 5)).resolve() == 0.0


def test_value_helpers() -> None:
    value = _bone().resolve()
    assert value.approx_equal(Segment2.between(Point2.at(0, 0), Point2.at(4, 0)).resolve())
    assert not value.approx_equal(Segment2Value(start=value.end, end=value.start))  # oriented
    assert repr(value) == "Segment2Value(start=[0, 0], end=[4, 0])"
