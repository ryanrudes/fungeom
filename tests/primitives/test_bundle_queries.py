"""The bundle query layer — BoolBundle, presence, map/distances, argmin/nearest, bounds, plane broadcasts."""

from __future__ import annotations

import numpy as np

from fungeom import (
    BoolBundle,
    Direction3,
    Plane,
    Point2Bundle,
    Point3,
    Point3Bundle,
    ScalarBundle,
    Unresolvable,
)
from fungeom.values import Point2Value, Point3Value


# --- C1: BoolBundle ---


def test_bool_bundle_logic_and_folds() -> None:
    a = BoolBundle.from_array([True, False, True], keys=["x", "y", "z"])
    b = BoolBundle.from_array([True, True, False], keys=["x", "y", "z"])
    assert a.at("x").resolve() is True
    assert (a & b).at("x").resolve() is True
    assert (a & b).at("y").resolve() is False
    assert (a | b).all().resolve() is True
    assert (~a).at("y").resolve() is True
    assert a.any().resolve() is True
    assert a.all().resolve() is False
    # the empty-fold identities: any(∅) = False, all(∅) = True
    assert BoolBundle.of([]).any().resolve() is False
    assert BoolBundle.of([]).all().resolve() is True


def test_bool_bundle_construction_masking_where_relabel() -> None:
    from fungeom import Bool, RosterMap

    masked = BoolBundle.from_map({"a": Bool.true}, roster=["a", "b"])
    assert masked.present("b").resolve() is False
    assert masked.any().resolve() is True  # only the present member counts
    trio = BoolBundle.from_array([True, False, True], keys=["a", "b", "c"])
    assert set(trio.where(["a", "b"]).support().resolve().keys) == {"a", "b"}
    relabeled = trio.relabel(RosterMap.of({"a": "A", "b": "B", "c": "C"}))
    assert relabeled.at("A").resolve() is True


# --- C2: presence mask ---


def test_presence_mask_and_all_any_present() -> None:
    cloud = Point3Bundle.from_map({"a": Point3.at(0, 0, 0)}, roster=["a", "b", "c"])
    mask = cloud.presence_mask()
    assert isinstance(mask, BoolBundle)
    assert mask.at("a").resolve() is True
    assert mask.at("b").resolve() is False  # declared but occluded → False, not dropped
    assert mask.count().resolve() == 3.0  # the mask is total over the roster
    assert cloud.all_present().resolve() is False
    assert cloud.any_present().resolve() is True
    full = Point3Bundle.from_array([[0, 0, 0], [1, 0, 0]])
    assert full.all_present().resolve() is True


# --- C3 / C4: map + distances_to ---


def test_map_and_distances_to() -> None:
    cloud = Point3Bundle.from_array([[0, 0, 0], [3, 4, 0]], keys=["a", "b"])
    origin = Point3.at(0, 0, 0)
    assert cloud.distances_to(origin).at("b").resolve() == 5.0
    assert cloud.map_scalar(lambda p: p.distance_to(origin)).at("b").resolve() == 5.0
    assert cloud.map_point(lambda p: p.midpoint(origin)).at("b").resolve().approx_equal(Point3Value.of(1.5, 2, 0))
    assert np.allclose(cloud.map_vec3(lambda p: p.displacement_to(origin)).at("b").resolve(), [-3, -4, 0])


# --- C5 / C6: argmin/argmax, nearest, closest ---


def test_argmin_argmax_return_a_singleton_roster() -> None:
    values = ScalarBundle.from_array([3.0, 1.0, 2.0], keys=["a", "b", "c"])
    assert values.argmin().resolve().keys == ("b",)
    assert values.argmax().resolve().keys == ("a",)
    # composes with where() to slice the winner
    assert set(values.where(values.argmin()).support().resolve().keys) == {"b"}
    # ties resolve to the first key in roster order
    tied = ScalarBundle.from_array([5.0, 5.0], keys=["first", "second"])
    assert tied.argmin().resolve().keys == ("first",)
    assert isinstance(ScalarBundle.of([]).argmin().decide(), Unresolvable)


def test_nearest_to_and_closest_point_to() -> None:
    cloud = Point3Bundle.from_array([[0, 0, 0], [3, 4, 0], [1, 1, 0]], keys=["a", "b", "c"])
    assert cloud.nearest_to(Point3.at(0, 0, 0)).resolve().keys == ("a",)
    assert cloud.closest_point_to(Point3.at(3, 3, 0)).resolve().approx_equal(Point3Value.of(3, 4, 0))
    assert isinstance(Point3Bundle.of([]).closest_point_to(Point3.at(0, 0, 0)).decide(), Unresolvable)


# --- C7: bounds ---


def test_bounds_of_3d_and_2d_clouds() -> None:
    cloud = Point3Bundle.from_array([[0, 0, 1], [3, 4, -2], [1, 1, 0]])
    box = cloud.bounds()
    assert box.at("min").resolve().approx_equal(Point3Value.of(0, 0, -2))
    assert box.at("max").resolve().approx_equal(Point3Value.of(3, 4, 1))
    flat = Point2Bundle.from_array([[0, 0], [3, 4]])
    assert flat.bounds().at("max").resolve().approx_equal(Point2Value.of(3, 4))
    assert isinstance(Point3Bundle.of([]).bounds().decide(), Unresolvable)
    assert isinstance(Point2Bundle.of([]).bounds().decide(), Unresolvable)


# --- G7: plane broadcasts ---


def test_plane_broadcasts_over_a_cloud() -> None:
    plane = Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1))  # z = 0
    cloud = Point3Bundle.from_map({"a": Point3.at(0, 0, 2), "b": Point3.at(1, 1, -1)}, roster=["a", "b", "occ"])
    heights = plane.signed_distance(cloud)
    assert isinstance(heights, ScalarBundle)
    assert heights.at("a").resolve() == 2.0
    assert heights.at("b").resolve() == -1.0
    assert heights.present("occ").resolve() is False  # the occlusion mask carries through
    # the footprint min-clearance idiom
    assert heights.min().resolve() == -1.0
    # project + contains broadcasts
    assert plane.project(cloud).at("a").resolve().approx_equal(Point3Value.of(0, 0, 0))
    on_plane = Point3Bundle.from_array([[1, 1, 0], [2, 2, 0.5]])
    assert isinstance(plane.contains(on_plane), BoolBundle)
    assert plane.contains(on_plane).at(0).resolve() is True
    assert plane.contains(on_plane).all().resolve() is False
    # the scalar overloads are unchanged
    assert plane.signed_distance(Point3.at(0, 0, 5)).resolve() == 5.0
    assert plane.contains(Point3.at(0, 0, 0)).resolve() is True
