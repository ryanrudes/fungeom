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


def test_to_local_and_embed_are_mutual_inverses() -> None:
    from fungeom import Point2

    # a tilted plane (so the chart is non-trivial)
    plane = Plane.through(Point3.at(1, 2, 3), Direction3.of(1, 1, 1))
    # embed a 2D point, flatten it back: round-trips exactly (2D → 3D → 2D)
    for uv in [(0.0, 0.0), (0.3, -0.7), (2.0, 1.5)]:
        world = plane.embed(Point2.at(*uv)).resolve()
        assert np.isclose(plane.signed_distance(Point3.at(*world.coord)).resolve(), 0.0)  # lands on the plane
        back = plane.to_local(Point3.at(*world.coord)).resolve()
        assert np.allclose(back.coord, uv)
    # an off-plane point flattens to the same chart coords as its projection (the normal is dropped)
    flat = Plane.through(Point3.at(0, 0, 3), Direction3.of(0, 0, 1))
    on = flat.to_local(Point3.at(5, 7, 3)).resolve().coord
    off = flat.to_local(Point3.at(5, 7, 99)).resolve().coord
    assert np.allclose(on, off)


def test_bridge_propagates_an_ungrounded_plane() -> None:
    from fungeom import CoordinateFrame, Point2

    loose = Point3.at(0, 0, 0, frame=CoordinateFrame.detached("loose"))
    ungrounded = Plane.through(loose, Direction3.of(0, 0, 1))
    assert isinstance(ungrounded.to_local(Point3.at(1, 1, 1)).decide(), Unresolvable)
    assert isinstance(ungrounded.embed(Point2.at(1, 1)).decide(), Unresolvable)


def test_winding_normal_orients_by_polygon_winding() -> None:
    g = _ground()  # the z = 5 plane, normal +z
    # a unit square traced counter-clockwise (seen from +z) winds toward +z
    square = [Point3.at(0, 0, 5), Point3.at(1, 0, 5), Point3.at(1, 1, 5), Point3.at(0, 1, 5)]
    assert np.allclose(g.winding_normal(square).resolve().vector, [0, 0, 1])
    assert np.allclose(g.winding_normal(list(reversed(square))).resolve().vector, [0, 0, -1])  # clockwise → -z
    # points off the plane are projected first, so the loop need not be exactly planar
    lifted = [Point3.at(0, 0, 9), Point3.at(1, 0, 2), Point3.at(1, 1, 7), Point3.at(0, 1, 4)]
    assert np.allclose(g.winding_normal(lifted).resolve().vector, [0, 0, 1])
    # the zero-area test is *relative* to scale (‖A‖ ≤ tol·maxradius²): a genuine but tiny
    # triangle still resolves — an absolute area threshold would wrongly reject it.
    tiny = [Point3.at(0, 0, 5), Point3.at(1e-5, 0, 5), Point3.at(0, 1e-5, 5)]
    assert np.allclose(g.winding_normal(tiny).resolve().vector, [0, 0, 1])


def test_winding_normal_partiality() -> None:
    g = _ground()
    too_few = g.winding_normal([Point3.at(0, 0, 5), Point3.at(1, 0, 5)])
    assert "at least three" in too_few.decide().reason
    # a collinear (zero-area) loop has no winding sense
    collinear = g.winding_normal([Point3.at(0, 0, 5), Point3.at(1, 0, 5), Point3.at(2, 0, 5)])
    decision = collinear.decide()
    assert isinstance(decision, Unresolvable)
    assert "no area" in decision.reason


def test_intersect_two_planes_meet_in_a_line() -> None:
    xy = Plane.through(Point3.at(0, 0, 5), Direction3.of(0, 0, 1))  # z = 5
    xz = Plane.through(Point3.at(0, 3, 0), Direction3.of(0, 1, 0))  # y = 3
    line = xy.intersect(xz)
    assert np.allclose(np.abs(line.direction().resolve().vector), [1, 0, 0])  # along x
    assert np.allclose(line.origin().resolve().coord, [0, 3, 5])  # the closest point to the origin
    assert xy.contains(line.origin()).resolve() and xz.contains(line.origin()).resolve()
    # parallel (and anti-parallel) planes never meet
    parallel = xy.intersect(Plane.through(Point3.at(0, 0, 9), Direction3.of(0, 0, 1)))
    decision = parallel.decide()
    assert isinstance(decision, Unresolvable)
    assert "parallel planes" in decision.reason
    assert isinstance(xy.intersect(xy.flipped()).decide(), Unresolvable)


def test_plane_value_helpers() -> None:
    value = _ground().resolve()
    assert value.approx_equal(Plane.through(Point3.at(9, 9, 5), Direction3.of(0, 0, 1)).resolve())  # same plane
    assert not value.approx_equal(value.flipped())  # oriented: a flip is a different plane
    assert repr(value) == "PlaneValue(point=[0, 0, 5], normal=[0, 0, 1])"


def test_zero_normal_is_rejected() -> None:
    # the value type enforces the unit-normal invariant (the facade never hits this)
    with pytest.raises(ValueError, match="zero normal"):
        PlaneValue(point=np.zeros(3), normal=np.zeros(3))
