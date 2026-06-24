"""Ray — a half-line and its algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction3, Plane, Point3, Ray, Unresolvable
from fungeom.values import RayValue


def _x_ray() -> Ray:
    # the +x half-line from the origin
    return Ray.through(Point3.at(0, 0, 0), Direction3.of(1, 0, 0))


def test_constructors() -> None:
    assert isinstance(_x_ray().resolve(), RayValue)
    from_to = Ray.from_to(Point3.at(0, 0, 0), Point3.at(0, 5, 0))
    assert np.allclose(from_to.direction().resolve().vector, [0, 1, 0])  # aimed origin → target


def test_constructor_partiality() -> None:
    coincident = Ray.from_to(Point3.at(1, 1, 1), Point3.at(1, 1, 1))
    assert "distinct from its origin" in coincident.decide().reason


def test_query() -> None:
    ray = _x_ray()
    assert np.allclose(ray.origin().resolve().coord, [0, 0, 0])
    assert np.allclose(ray.direction().resolve().vector, [1, 0, 0])
    # ahead of the origin: an ordinary perpendicular projection
    assert np.allclose(ray.project(Point3.at(3, 2, 0)).resolve().coord, [3, 0, 0])
    assert ray.distance_to(Point3.at(3, 4, 0)).resolve() == 4.0
    assert ray.contains(Point3.at(7, 0, 0)).resolve() is True


def test_clamps_behind_the_origin() -> None:
    ray = _x_ray()
    # a point behind the origin projects to the origin, not onto the back-extension
    assert np.allclose(ray.project(Point3.at(-3, 2, 0)).resolve().coord, [0, 0, 0])
    assert ray.distance_to(Point3.at(-3, 4, 0)).resolve() == 5.0  # distance to the origin, √(3²+4²)
    assert ray.contains(Point3.at(-5, 0, 0)).resolve() is False  # on the line, but behind the start


def test_point_at() -> None:
    ray = _x_ray()
    assert np.allclose(ray.point_at(4.0).resolve().coord, [4, 0, 0])
    decision = ray.point_at(-1.0).decide()  # off the half-line
    assert isinstance(decision, Unresolvable)
    assert "negative distance" in decision.reason


def test_reversed() -> None:
    ray = _x_ray()
    reversed_ray = ray.reversed()
    assert np.allclose(reversed_ray.direction().resolve().vector, [-1, 0, 0])
    assert np.allclose(reversed_ray.origin().resolve().coord, [0, 0, 0])  # same origin


def test_intersect_plane_is_the_raycast() -> None:
    floor = Plane.through(Point3.at(0, 0, 5), Direction3.of(0, 0, 1))  # z = 5
    up = Ray.through(Point3.at(0, 0, 0), Direction3.of(1, 0, 1))  # oblique, toward +z
    assert np.allclose(up.intersect(floor).resolve().coord, [5, 0, 5])
    # a ray starting on the plane hits at its origin (t = 0)
    assert np.allclose(
        Ray.through(Point3.at(0, 0, 5), Direction3.of(0, 0, 1)).intersect(floor).resolve().coord, [0, 0, 5]
    )
    # pointing away → the plane is behind the origin
    away = Ray.through(Point3.at(0, 0, 0), Direction3.of(0, 0, -1)).intersect(floor)
    assert isinstance(away.decide(), Unresolvable)
    assert "behind the ray" in away.decide().reason
    # parallel to the plane → no unique hit
    parallel = Ray.through(Point3.at(0, 0, 0), Direction3.of(1, 0, 0)).intersect(floor)
    assert isinstance(parallel.decide(), Unresolvable)
    assert "parallel to the plane" in parallel.decide().reason


def test_ray_value_helpers() -> None:
    value = _x_ray().resolve()
    assert value.approx_equal(Ray.through(Point3.at(0, 0, 0), Direction3.of(2, 0, 0)).resolve())
    assert not value.approx_equal(value.reversed())  # a ray's direction matters
    # a ray's origin matters too: a shifted origin is a different ray (unlike a line)
    assert not value.approx_equal(Ray.through(Point3.at(5, 0, 0), Direction3.of(1, 0, 0)).resolve())
    assert repr(value) == "RayValue(origin=[0, 0, 0], direction=[1, 0, 0])"


def test_zero_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero direction"):
        RayValue(point=np.zeros(3), direction=np.zeros(3))
