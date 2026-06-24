"""Segment — a finite line segment and its algebra."""

from __future__ import annotations

import numpy as np

from fungeom import Point3, Segment, Unresolvable
from fungeom.values import SegmentValue


def _bone() -> Segment:
    # a 4-long segment along +x (a bone from one joint to another)
    return Segment.between(Point3.at(0, 0, 0), Point3.at(4, 0, 0))


def test_constructor_and_shape() -> None:
    bone = _bone()
    assert isinstance(bone.resolve(), SegmentValue)
    assert bone.length().resolve() == 4.0
    assert np.allclose(bone.midpoint().resolve().coord, [2, 0, 0])
    assert np.allclose(bone.direction().resolve().vector, [1, 0, 0])
    assert np.allclose(bone.start().resolve().coord, [0, 0, 0])
    assert np.allclose(bone.end().resolve().coord, [4, 0, 0])


def test_query_clamps_to_the_endpoints() -> None:
    bone = _bone()
    assert np.allclose(bone.project(Point3.at(1, 5, 0)).resolve().coord, [1, 0, 0])  # interior foot
    assert np.allclose(bone.project(Point3.at(9, 5, 0)).resolve().coord, [4, 0, 0])  # clamps past the end
    assert np.allclose(bone.project(Point3.at(-9, 5, 0)).resolve().coord, [0, 0, 0])  # clamps before the start
    assert bone.distance_to(Point3.at(9, 3, 0)).resolve() == np.hypot(5.0, 3.0)  # to the end, not the line
    assert bone.contains(Point3.at(2, 0, 0)).resolve() is True
    assert bone.contains(Point3.at(9, 0, 0)).resolve() is False  # on the line, past the end


def test_at_and_parameter_of() -> None:
    bone = _bone()
    assert np.allclose(bone.at(0.25).resolve().coord, [1, 0, 0])
    assert bone.parameter_of(Point3.at(3, 0, 0)).resolve() == 0.75
    assert bone.parameter_of(Point3.at(9, 0, 0)).resolve() == 1.0  # clamped
    decision = bone.at(1.5).decide()  # off the segment
    assert isinstance(decision, Unresolvable)
    assert "outside [0, 1]" in decision.reason


def test_degenerate_segment_has_no_direction() -> None:
    point = Segment.between(Point3.at(2, 2, 2), Point3.at(2, 2, 2))
    assert point.length().resolve() == 0.0  # still a valid (degenerate) value
    decision = point.direction().decide()
    assert isinstance(decision, Unresolvable)
    assert "zero-length" in decision.reason
    # queries still resolve: a degenerate segment collapses to its single location
    assert np.allclose(point.project(Point3.at(5, 5, 5)).resolve().coord, [2, 2, 2])
    assert point.parameter_of(Point3.at(5, 5, 5)).resolve() == 0.0


def test_reversed() -> None:
    bone = _bone()
    flipped = bone.reversed()
    assert np.allclose(flipped.start().resolve().coord, [4, 0, 0])
    assert np.allclose(flipped.direction().resolve().vector, [-1, 0, 0])


def test_segment_value_helpers() -> None:
    value = _bone().resolve()
    assert value.approx_equal(Segment.between(Point3.at(0, 0, 0), Point3.at(4, 0, 0)).resolve())
    assert not value.approx_equal(SegmentValue(start=value.end, end=value.start))  # oriented
    assert repr(value) == "SegmentValue(start=[0, 0, 0], end=[4, 0, 0])"
