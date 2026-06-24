"""Plane — an oriented plane and its surface algebra."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import Direction3, Plane, Point3, Unresolvable, Vec3
from fungeom.values import PlaneValue


def _ground() -> Plane:
    # the z = 5 plane, normal +z
    return Plane.through(Point3.at(0, 0, 5), Direction3.of(0, 0, 1))


def test_constructors() -> None:
    assert isinstance(_ground().resolve(), PlaneValue)
    fitted = Plane.through_points(Point3.at(0, 0, 0), Point3.at(1, 0, 0), Point3.at(0, 1, 0))
    assert np.allclose(fitted.normal().resolve().vector, [0, 0, 1])  # right-hand rule
    spanned = Plane.spanned_by(Point3.at(0, 0, 0), Vec3.of(1, 0, 0), Vec3.of(0, 1, 0))
    assert np.allclose(spanned.normal().resolve().vector, [0, 0, 1])


def test_constructor_partiality() -> None:
    collinear = Plane.through_points(Point3.at(0, 0, 0), Point3.at(1, 0, 0), Point3.at(2, 0, 0))
    assert "collinear" in collinear.decide().reason
    parallel = Plane.spanned_by(Point3.at(0, 0, 0), Vec3.of(1, 0, 0), Vec3.of(2, 0, 0))
    assert "parallel" in parallel.decide().reason


def test_query() -> None:
    g = _ground()
    assert g.signed_distance(Point3.at(0, 0, 8)).resolve() == 3.0
    assert g.signed_distance(Point3.at(0, 0, 2)).resolve() == -3.0
    assert np.allclose(g.project(Point3.at(2, 3, 8)).resolve().coord, [2, 3, 5])
    assert g.distance_to(Point3.at(0, 0, 2)).resolve() == 3.0
    assert g.contains(Point3.at(7, 7, 5)).resolve() is True
    assert g.contains(Point3.at(0, 0, 6)).resolve() is False
    assert np.allclose(g.origin().resolve().coord, [0, 0, 5])


def test_facing_resolves_the_normal_sign() -> None:
    g = _ground()  # normal +z
    assert np.allclose(g.facing(Point3.at(0, 0, 9)).normal().resolve().vector, [0, 0, 1])  # above → unchanged
    assert np.allclose(g.facing(Point3.at(0, 0, 1)).normal().resolve().vector, [0, 0, -1])  # below → flipped
    # a point on the plane has no side
    decision = g.facing(Point3.at(1, 1, 5)).decide()
    assert isinstance(decision, Unresolvable)
    assert "lies on the plane" in decision.reason


def test_flipped_and_offset() -> None:
    g = _ground()
    assert np.allclose(g.flipped().normal().resolve().vector, [0, 0, -1])
    # offset +2 along +z moves the plane to z = 7, so the old anchor at z = 5 is now -2 away
    assert g.offset(2.0).signed_distance(Point3.at(0, 0, 5)).resolve() == -2.0


def test_project_direction() -> None:
    g = _ground()
    assert np.allclose(g.project_direction(Direction3.of(1, 0, 1)).resolve().vector, [1, 0, 0])  # drops the z part
    decision = g.project_direction(Direction3.of(0, 0, 1)).decide()  # parallel to normal
    assert isinstance(decision, Unresolvable)
    assert "no in-plane component" in decision.reason


def test_frame_is_the_canonical_surface_frame() -> None:
    g = _ground()
    # a tangent with a normal component, so the in-plane (Gram-Schmidt) projection is load-bearing
    transform = g.frame(Point3.at(1, 2, 5), Direction3.of(1, 0, 1)).resolve()
    rotation = transform.rotation
    assert np.allclose(transform.translation, [1, 2, 5])
    assert np.allclose(rotation[:, 2], [0, 0, 1])  # +z = normal
    assert np.allclose(rotation[:, 0], [1, 0, 0])  # +x = tangent's *in-plane* part (the z is dropped)
    assert np.allclose(rotation[:, 1], [0, 1, 0])  # +y = z × x
    assert np.allclose(rotation.T @ rotation, np.eye(3))  # orthonormal...
    assert np.isclose(np.linalg.det(rotation), 1.0)  # ...and proper (right-handed)
    # a tangent parallel to the normal has no in-plane x axis
    decision = g.frame(Point3.at(0, 0, 5), Direction3.of(0, 0, 1)).decide()
    assert isinstance(decision, Unresolvable)
    assert "no in-plane x axis" in decision.reason


def test_plane_value_helpers() -> None:
    value = _ground().resolve()
    assert value.approx_equal(Plane.through(Point3.at(9, 9, 5), Direction3.of(0, 0, 1)).resolve())  # same plane
    assert not value.approx_equal(value.flipped())  # oriented: a flip is a different plane
    assert repr(value) == "PlaneValue(point=[0, 0, 5], normal=[0, 0, 1])"


def test_zero_normal_is_rejected() -> None:
    # the value type enforces the unit-normal invariant (the facade never hits this)
    with pytest.raises(ValueError, match="zero normal"):
        PlaneValue(point=np.zeros(3), normal=np.zeros(3))
