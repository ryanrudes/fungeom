"""Face — an oriented bounded patch (a Plane carrying a Region2): the honest bounded clearance."""

from __future__ import annotations

import numpy as np

from fungeom import (
    Direction3,
    Face,
    Plane,
    Point3,
    Region2,
    Unresolvable,
)
from fungeom.values import FaceValue


def _patch() -> Face:
    # the z = 0 plane carrying a 4 × 2 rectangle in its chart
    plane = Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1))
    return Face.on(plane, Region2.rectangle(4, 2))


def test_construction_and_accessors() -> None:
    patch = _patch()
    assert isinstance(patch.resolve(), FaceValue)
    assert patch.region().area().resolve() == 8.0
    assert np.allclose(patch.plane().normal().resolve().vector, [0, 0, 1])


def test_clearance_above_the_patch_is_the_height() -> None:
    patch = _patch()
    above = Point3.at(0.5, 0.3, 2.0)  # projects to inside the patch
    assert patch.clearance(above).resolve() == 2.0
    # the closest point is directly below, on the plane
    assert patch.closest_point(above).resolve().approx_equal(Point3.at(0.5, 0.3, 0.0).resolve())


def test_clearance_beside_the_patch_clamps_to_the_edge() -> None:
    patch = _patch()
    plane = patch.plane()
    beside = Point3.at(10, 0, 2.0)  # projects far outside the rectangle
    # the honest bounded clearance is larger than the infinite-plane distance (the whole point of Face)
    bounded = patch.clearance(beside).resolve()
    assert bounded > plane.distance_to(beside).resolve()
    # …and it is exactly the 3-D distance to the clamped closest point (a real surface point on the plane)
    closest = patch.closest_point(beside).resolve()
    assert np.isclose(plane.signed_distance(Point3.at(*closest.coord)).resolve(), 0.0)
    assert np.isclose(bounded, np.linalg.norm(np.array([10, 0, 2.0]) - closest.coord))


def test_empty_face_has_no_surface() -> None:
    plane = Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1))
    empty = Face.on(plane, Region2.empty)
    assert isinstance(empty.clearance(Point3.at(0, 0, 1)).decide(), Unresolvable)
    assert isinstance(empty.closest_point(Point3.at(0, 0, 1)).decide(), Unresolvable)


def test_propagates_an_ungrounded_plane() -> None:
    from fungeom import CoordinateFrame

    loose = Point3.at(0, 0, 0, frame=CoordinateFrame.detached("loose"))
    bad_plane = Plane.through(loose, Direction3.of(0, 0, 1))
    patch = Face.on(bad_plane, Region2.rectangle(2, 2))
    assert isinstance(patch.decide(), Unresolvable)
    assert isinstance(patch.clearance(Point3.at(0, 0, 1)).decide(), Unresolvable)
    assert isinstance(patch.region().decide(), Unresolvable)  # the accessor propagates too


def test_repr() -> None:
    assert "FaceValue" in repr(_patch().resolve())


def test_contains_is_footprint_membership() -> None:
    patch = _patch()  # the z=0 plane carrying a 4×2 rectangle
    assert patch.contains(Point3.at(1, 0.5, 5.0)).resolve() is True  # projects inside (normal offset ignored)
    assert patch.contains(Point3.at(1, 0.5, -3.0)).resolve() is True  # …from either side
    assert patch.contains(Point3.at(10, 0, 0)).resolve() is False  # projects outside the footprint
    # total — an empty patch has no footprint, so contains is False (not Unresolvable)
    empty = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty)
    assert empty.contains(Point3.at(0, 0, 0)).resolve() is False


def test_transformed_by_transports_the_patch() -> None:
    from fungeom import Transform

    patch = _patch()  # z = 0 plane, 4×2 rectangle
    moved = patch.transformed_by(Transform.translation([0, 0, 3]))  # lift the whole patch +3z
    # a point 5 above the original now sits 2 above the moved patch
    assert np.isclose(moved.clearance(Point3.at(0.5, 0.3, 5.0)).resolve(), 2.0)
    assert np.allclose(moved.plane().normal().resolve().vector, [0, 0, 1])  # the region is kept (plane-local)


def test_frame_is_deterministic_with_normal_as_z() -> None:
    patch = _patch()
    frame = patch.frame().resolve()
    assert np.allclose(frame.rotation[:, 2], [0, 0, 1])  # +z column = the plane normal
    assert frame.approx_equal(patch.frame().resolve())  # deterministic: same face → same frame
    # an empty patch has no centroid, so no frame
    empty = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty)
    assert isinstance(empty.frame().decide(), Unresolvable)


def test_boundary_embeds_the_footprint_vertices() -> None:
    patch = _patch()  # 4×2 rectangle on z = 0 → 4 corners
    boundary = patch.boundary()
    assert boundary.count().resolve() == 4
    # every corner lies on the plane (z = 0)
    for key in range(4):
        assert np.isclose(boundary.at(key).resolve().coord[2], 0.0)
