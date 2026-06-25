"""Region2 — the bounded planar region (the 2D spatial sibling of Coverage)."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    Direction3,
    Plane,
    Point2,
    Point2Bundle,
    Point3,
    Region2,
    Transform2,
    Unresolvable,
)
from fungeom.values import Point2Value, Region2Value


def test_rectangle_area_centroid_contains() -> None:
    rect = Region2.rectangle(4, 2)
    assert rect.area().resolve() == 8.0
    assert rect.centroid().resolve().approx_equal(Point2Value.of(0, 0))
    assert rect.contains(Point2.at(0, 0)).resolve() is True
    assert rect.contains(Point2.at(3, 0)).resolve() is False  # outside (half-width is 2)
    assert rect.contains(Point2.at(2, 0)).resolve() is True  # on the boundary → contained
    off = Region2.rectangle(2, 2, center=(10, 5))
    assert off.centroid().resolve().approx_equal(Point2Value.of(10, 5))


def test_rectangle_partiality() -> None:
    assert "positive extents" in Region2.rectangle(0, 2).decide().reason
    assert isinstance(Region2.rectangle(2, -1).decide(), Unresolvable)


def test_disc_approximates_a_circle() -> None:
    disc = Region2.disc(1.0, segments=256)
    assert np.isclose(disc.area().resolve(), np.pi, atol=1e-3)
    assert disc.contains(Point2.at(0, 0)).resolve() is True
    assert disc.contains(Point2.at(0.9, 0)).resolve() is True
    assert disc.contains(Point2.at(1.5, 0)).resolve() is False
    assert disc.vertices().count().resolve() == 256.0


def test_disc_partiality() -> None:
    assert "positive radius" in Region2.disc(0).decide().reason
    assert "at least 3 segments" in Region2.disc(1.0, segments=2).decide().reason


def test_polygon_area_centroid_and_orientation() -> None:
    tri = Region2.polygon([Point2.at(0, 0), Point2.at(4, 0), Point2.at(0, 3)])
    assert tri.area().resolve() == 6.0
    assert tri.centroid().resolve().approx_equal(Point2Value.of(4 / 3, 1))
    # a clockwise winding is normalized to a positive-area region (orientation is fixed up)
    cw = Region2.polygon([Point2.at(0, 0), Point2.at(0, 3), Point2.at(4, 0)])
    assert cw.area().resolve() == 6.0


def test_polygon_partiality() -> None:
    assert "at least 3 vertices" in Region2.polygon([Point2.at(0, 0), Point2.at(1, 1)]).decide().reason
    coincident = Region2.polygon([Point2.at(0, 0), Point2.at(0, 0), Point2.at(1, 1)])
    assert "coincident consecutive" in coincident.decide().reason
    collinear = Region2.polygon([Point2.at(0, 0), Point2.at(1, 0), Point2.at(2, 0)])
    assert "no area" in collinear.decide().reason
    # a pentagram: a self-intersecting loop with non-zero area — the simplicity check fires
    angles = np.deg2rad(90 + 72 * np.arange(5))
    pentagon = np.column_stack([np.cos(angles), np.sin(angles)])
    star = pentagon[[0, 2, 4, 1, 3]]
    pentagram = Region2.polygon([Point2.at(float(x), float(y)) for x, y in star])
    assert "self-intersecting" in pentagram.decide().reason


def test_hull_from_a_sequence_drops_interior_points() -> None:
    hull = Region2.hull([Point2.at(0, 0), Point2.at(4, 0), Point2.at(4, 3), Point2.at(0, 3), Point2.at(2, 1)])
    assert hull.area().resolve() == 12.0  # the interior (2,1) does not change the hull
    assert hull.vertices().count().resolve() == 4.0


def test_hull_from_a_bundle_uses_present_members() -> None:
    cloud = Point2Bundle.from_map(
        {"a": Point2.at(0, 0), "b": Point2.at(4, 0), "c": Point2.at(4, 3), "d": Point2.at(0, 3)},
        roster=["a", "b", "c", "d", "occluded"],
    )
    hull = Region2.hull(cloud)
    assert hull.area().resolve() == 12.0  # the occluded marker is simply absent


def test_hull_partiality() -> None:
    assert "at least 3 points" in Region2.hull([Point2.at(0, 0), Point2.at(1, 1)]).decide().reason
    collinear = Region2.hull([Point2.at(0, 0), Point2.at(1, 0), Point2.at(2, 0)])
    assert "no 2D convex hull" in collinear.decide().reason
    # a degenerate bundle (too few present) is Unresolvable, not a silent empty region
    sparse = Point2Bundle.from_map({"a": Point2.at(0, 0)}, roster=["a", "b", "c"])
    assert isinstance(Region2.hull(sparse).decide(), Unresolvable)


def test_vertices_and_bounds() -> None:
    rect = Region2.rectangle(4, 2, center=(1, 1))
    corners = rect.vertices()
    assert corners.count().resolve() == 4.0
    box = rect.bounds()
    assert box.at("min").resolve().approx_equal(Point2Value.of(-1, 0))
    assert box.at("max").resolve().approx_equal(Point2Value.of(3, 2))


def test_transformed_by_moves_and_rotates() -> None:
    rect = Region2.rectangle(2, 2)
    moved = rect.transformed_by(Transform2.translation((10, 0)))
    assert moved.centroid().resolve().approx_equal(Point2Value.of(10, 0))
    assert moved.area().resolve() == 4.0  # rigid motion preserves area
    turned = rect.transformed_by(Transform2.rotation(np.pi / 4))
    assert np.isclose(turned.area().resolve(), 4.0)


def test_signed_distance_is_the_stability_margin() -> None:
    rect = Region2.rectangle(4, 2)  # [-2, 2] × [-1, 1]
    # inside → positive, the distance to the nearest edge
    assert rect.signed_distance(Point2.at(0, 0)).resolve() == 1.0
    assert rect.signed_distance(Point2.at(1.5, 0)).resolve() == 0.5
    # on the boundary → zero
    assert np.isclose(rect.signed_distance(Point2.at(2, 0)).resolve(), 0.0)
    # outside → negative, beside an edge or off a corner
    assert rect.signed_distance(Point2.at(4, 0)).resolve() == -2.0
    assert np.isclose(rect.signed_distance(Point2.at(4, 4)).resolve(), -np.hypot(2, 3))


def test_nearest_boundary_point() -> None:
    rect = Region2.rectangle(4, 2)
    assert rect.nearest_boundary_point(Point2.at(4, 0)).resolve().approx_equal(Point2Value.of(2, 0))  # beside an edge
    assert rect.nearest_boundary_point(Point2.at(4, 4)).resolve().approx_equal(Point2Value.of(2, 1))  # off a corner
    inside = rect.nearest_boundary_point(Point2.at(0, 0.5)).resolve()  # interior point projects to the closest edge
    assert inside.approx_equal(Point2Value.of(0, 1))


def test_distance_extensions_empty_is_unresolvable() -> None:
    assert isinstance(Region2.empty.signed_distance(Point2.at(0, 0)).decide(), Unresolvable)
    assert isinstance(Region2.empty.nearest_boundary_point(Point2.at(0, 0)).decide(), Unresolvable)


def _ell() -> Region2:
    # an L-shaped (non-convex) simple polygon, area 5
    return Region2.polygon(
        [Point2.at(0, 0), Point2.at(3, 0), Point2.at(3, 1), Point2.at(1, 1), Point2.at(1, 3), Point2.at(0, 3)]
    )


def test_offset_erodes_and_dilates() -> None:
    rect = Region2.rectangle(4, 2)  # → [-2,2] × [-1,1]
    eroded = rect.offset(-0.5)  # erosion of a convex shape keeps sharp corners → an inset 3 × 1
    assert np.isclose(eroded.area().resolve(), 3.0)
    assert eroded.bounds().at("min").resolve().approx_equal(Point2Value.of(-1.5, -0.5))
    # dilation is the Minkowski sum with a disc — rounded corners (area = base + perimeter·d + π·d²)
    dilated = rect.offset(0.5)
    assert np.isclose(dilated.area().resolve(), 8 + 12 * 0.5 + np.pi * 0.5**2, atol=0.01)
    # erosion past extinction → the empty region; the empty region offsets to itself
    assert rect.offset(-5).resolve().is_empty
    assert Region2.empty.offset(0.3).resolve().is_empty


def test_offset_is_general() -> None:
    # a non-convex (L-shaped) region offsets fine now (was convex-only before shapely)
    eroded = _ell().offset(-0.2)
    assert 2.0 < eroded.area().resolve() < 5.0  # eroded, smaller than the original area 5
    # a region with a hole also offsets
    holey = Region2.rectangle(6, 6).difference(Region2.rectangle(2, 2))  # area 32
    assert holey.offset(-0.1).area().resolve() < 32.0


def test_intersection_of_regions() -> None:
    a = Region2.rectangle(4, 4)  # [-2,2]²
    inside = Region2.rectangle(2, 2, center=(1, 1))  # ⊂ a
    overlap = Region2.rectangle(4, 4, center=(3, 0))  # [1,5]×[-2,2], partial overlap
    disjoint = Region2.rectangle(2, 2, center=(10, 10))
    assert a.intersection(inside).area().resolve() == 4.0
    assert np.isclose(a.intersection(overlap).area().resolve(), 4.0)  # [1,2]×[-2,2]
    assert a.intersection(disjoint).resolve().is_empty  # disjoint → empty
    assert a.intersection(Region2.empty).resolve().is_empty  # empty operand → empty
    assert a.intersection(_ell()).area().resolve() < 4.0  # a non-convex operand works
    # regions touching only along an edge meet in a measure-zero set → the empty region
    edge_touch = Region2.rectangle(4, 4, center=(4, 0))  # shares the x = 2 edge with a
    assert a.intersection(edge_touch).resolve().is_empty


def test_union_of_regions() -> None:
    a = Region2.rectangle(4, 4)
    inside = Region2.rectangle(2, 2, center=(1, 1))
    disjoint = Region2.rectangle(2, 2, center=(10, 10))
    assert a.union(inside).area().resolve() == 16.0  # the larger swallows the contained one
    merged = a.union(disjoint)
    assert merged.area().resolve() == 20.0  # disjoint → a multipolygon (16 + 4)
    assert merged.contains(Point2.at(10, 10)).resolve() is True  # both lobes are in the region
    assert merged.contains(Point2.at(0, 0)).resolve() is True
    # a partial overlap merges into a single (non-convex) outline — now general, not Unresolvable
    assert a.union(Region2.rectangle(4, 4, center=(3, 0))).area().resolve() == 28.0  # 16 + 16 − 4
    assert a.union(Region2.empty).resolve().approx_equal(a.resolve())  # empty identity


def test_difference_punches_a_hole_and_clips() -> None:
    a = Region2.rectangle(4, 4)  # area 16
    hole = Region2.rectangle(2, 2, center=(1, 1))  # ⊂ a, area 4
    punched = a.difference(hole)
    assert punched.area().resolve() == 12.0
    assert punched.contains(Point2.at(1, 1)).resolve() is False  # inside the hole → out
    assert punched.contains(Point2.at(-1.5, -1.5)).resolve() is True  # in the solid part → in
    # disjoint subtrahend leaves the region unchanged; self-difference is empty
    assert a.difference(Region2.rectangle(2, 2, center=(10, 10))).area().resolve() == 16.0
    assert a.difference(a).resolve().is_empty
    assert Region2.empty.difference(a).resolve().is_empty
    # a partial overlap clips correctly — now general, not Unresolvable
    assert a.difference(Region2.rectangle(4, 4, center=(3, 0))).area().resolve() == 12.0  # 16 − 4


def test_boolean_ops_propagate_unresolvable_operands() -> None:
    from fungeom import Frame2

    bad = Region2.polygon([Point2.at(0, 0, frame=Frame2.detached("loose")), Point2.at(1, 0), Point2.at(0, 1)])
    good = Region2.rectangle(2, 2)
    assert isinstance(bad.union(good).decide(), Unresolvable)
    assert isinstance(good.intersection(bad).decide(), Unresolvable)
    assert isinstance(bad.difference(good).decide(), Unresolvable)


def test_the_full_patch_headline() -> None:
    # hull(markers).offset(-).difference(disc) — the retarget patch-definition headline
    markers = Point2Bundle.from_array([[0, 0], [0.2, 0], [0.2, 0.1], [0, 0.1]])
    region = Region2.hull(markers).offset(-0.005).difference(Region2.disc(0.01, center=(0.1, 0.05)))
    assert region.area().resolve() < 0.2 * 0.1  # smaller than the raw hull (eroded, with a hole)
    assert region.contains(Point2.at(0.1, 0.05)).resolve() is False  # the punched hole


def test_sample_and_corners() -> None:
    rect = Region2.rectangle(4, 2)
    samples = rect.sample(8)
    assert samples.count().resolve() == 8.0
    # samples lie on the boundary (signed distance ≈ 0)
    for key in range(8):
        assert np.isclose(rect.signed_distance(samples.at(key)).resolve(), 0.0, atol=1e-9)
    assert rect.corners().count().resolve() == 4.0  # alias of vertices
    assert isinstance(rect.sample(0).decide(), Unresolvable)  # non-positive count
    assert isinstance(Region2.empty.sample(4).decide(), Unresolvable)  # empty boundary


def test_empty_region() -> None:
    empty = Region2.empty
    assert empty.area().resolve() == 0.0
    assert empty.vertices().count().resolve() == 0.0
    assert isinstance(empty.centroid().decide(), Unresolvable)
    assert isinstance(empty.bounds().decide(), Unresolvable)
    assert empty.contains(Point2.at(0, 0)).resolve() is False
    assert "empty" in repr(empty.resolve())


def test_value_helpers_directly() -> None:
    # the value's own guards (the dead-via-facade direct-caller paths)
    with pytest.raises(ValueError, match="empty region"):
        Region2Value(rings=()).centroid()
    with pytest.raises(ValueError, match="empty region"):
        Region2Value(rings=()).bounds()
    with pytest.raises(ValueError, match="no boundary"):
        Region2Value(rings=()).nearest_boundary_point((0, 0))
    square = Region2.rectangle(2, 2).resolve()
    assert square.approx_equal(square)
    assert not square.approx_equal(Region2.rectangle(4, 4).resolve())  # different vertices, same vertex count
    triangle = Region2.polygon([Point2.at(0, 0), Point2.at(1, 0), Point2.at(0, 1)]).resolve()
    assert not square.approx_equal(triangle)  # same ring count, different vertex count (_rings_match length guard)
    assert not square.approx_equal(Region2Value(rings=()))  # different ring count
    assert "ring(s)" in repr(square)  # the non-empty repr
    assert "empty" in repr(Region2Value(rings=()))


def test_propagation_through_a_plane_bridge() -> None:
    # the headline use: flatten 3D markers into a plane, hull them into a patch region
    plane = Plane.through(Point3.at(0, 0, 3), Direction3.of(0, 0, 1))
    cloud = Point2Bundle.from_array([[0, 0], [4, 0], [4, 3], [0, 3]])
    region = Region2.hull(cloud)
    embedded = plane.embed(region.centroid()).resolve()
    assert np.isclose(embedded.coord[2], 3.0)  # the region centroid lifts back onto the plane
