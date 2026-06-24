"""Ray2 — a 2D half-line and its algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction2, Line2, Point2, Ray2, Unresolvable
from fungeom.values import Ray2Value


def _x_ray() -> Ray2:
    return Ray2.through(Point2.at(0, 0), Direction2.of(1, 0))


def test_constructors_and_query() -> None:
    assert isinstance(_x_ray().resolve(), Ray2Value)
    from_to = Ray2.from_to(Point2.at(0, 0), Point2.at(0, 5))
    assert np.allclose(from_to.direction().resolve().vector, [0, 1])
    ray = _x_ray()
    assert np.allclose(ray.origin().resolve().coord, [0, 0])
    assert np.allclose(ray.project(Point2.at(3, 2)).resolve().coord, [3, 0])  # ahead
    assert ray.distance_to(Point2.at(3, 4)).resolve() == 4.0
    assert ray.contains(Point2.at(7, 0)).resolve() is True


def test_clamps_behind_the_origin() -> None:
    ray = _x_ray()
    assert np.allclose(ray.project(Point2.at(-3, 2)).resolve().coord, [0, 0])  # clamps to origin
    assert ray.distance_to(Point2.at(-3, 4)).resolve() == 5.0  # to the origin, √(3²+4²)
    assert ray.contains(Point2.at(-5, 0)).resolve() is False  # on the line but behind the start


def test_point_at_and_reversed_and_partiality() -> None:
    ray = _x_ray()
    assert np.allclose(ray.point_at(4.0).resolve().coord, [4, 0])
    assert isinstance(ray.point_at(-1.0).decide(), Unresolvable)
    assert np.allclose(ray.reversed().direction().resolve().vector, [-1, 0])
    assert "distinct from its origin" in Ray2.from_to(Point2.at(1, 1), Point2.at(1, 1)).decide().reason


def test_intersect_line_is_the_planar_raycast() -> None:
    wall = Line2.through(Point2.at(5, 0), Direction2.of(0, 1))  # the vertical line x = 5
    hit = Ray2.through(Point2.at(0, 0), Direction2.of(1, 0)).intersect(wall)  # +x ray
    assert np.allclose(hit.resolve().coord, [5, 0])
    # pointing away → the line is behind the origin
    away = Ray2.through(Point2.at(0, 0), Direction2.of(-1, 0)).intersect(wall)
    assert isinstance(away.decide(), Unresolvable)
    assert "behind the ray" in away.decide().reason
    # parallel to the line → no unique hit
    parallel = Ray2.through(Point2.at(0, 0), Direction2.of(0, 1)).intersect(wall)
    assert isinstance(parallel.decide(), Unresolvable)
    assert "parallel to the line" in parallel.decide().reason


def test_value_helpers() -> None:
    value = _x_ray().resolve()
    assert value.approx_equal(Ray2.through(Point2.at(0, 0), Direction2.of(2, 0)).resolve())
    assert not value.approx_equal(value.reversed())  # direction matters
    assert not value.approx_equal(Ray2.through(Point2.at(5, 0), Direction2.of(1, 0)).resolve())  # origin matters
    assert repr(value) == "Ray2Value(origin=[0, 0], direction=[1, 0])"


def test_zero_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero direction"):
        Ray2Value(point=np.zeros(2), direction=np.zeros(2))
