"""Point2Bundle — the planar point cloud (the 2D sibling of Point3Bundle)."""

from __future__ import annotations

import numpy as np

from fungeom import (
    Point2,
    Point2Bundle,
    RosterMap,
    Transform2,
    Unresolvable,
)
from fungeom.values import BundleValue, Point2Value


def _cloud() -> Point2Bundle:
    return Point2Bundle.of([Point2.at(0, 0), Point2.at(4, 0), Point2.at(0, 3)])


def test_positional_construction_and_at() -> None:
    cloud = _cloud()
    assert isinstance(cloud.resolve(), BundleValue)
    assert cloud.at(1).resolve().approx_equal(Point2Value.of(4, 0))
    assert cloud.count().resolve() == 3.0


def test_from_array_construction() -> None:
    cloud = Point2Bundle.from_array([[0, 0], [4, 0], [0, 3]])
    assert cloud.at(2).resolve().approx_equal(Point2Value.of(0, 3))
    keyed = Point2Bundle.from_array([[1, 0], [0, 2]], keys=["a", "b"])
    assert keyed.at("a").resolve().approx_equal(Point2Value.of(1, 0))


def test_keyed_construction_and_support() -> None:
    cloud = Point2Bundle.from_map({"a": Point2.at(1, 0), "b": Point2.at(0, 2)})
    assert cloud.at("b").resolve().approx_equal(Point2Value.of(0, 2))
    assert set(cloud.support().resolve().keys) == {"a", "b"}


def test_masking_via_a_wider_roster() -> None:
    cloud = Point2Bundle.from_map({"a": Point2.at(1, 1)}, roster=["a", "x"])
    assert cloud.present("a").resolve() is True
    assert cloud.present("x").resolve() is False  # in the roster but absent
    assert cloud.present("nope").resolve() is False  # not even in the roster
    assert cloud.count().resolve() == 1.0
    assert isinstance(cloud.at("x").decide(), Unresolvable)  # absent → no value


def test_centroid_folds_over_present_members() -> None:
    cloud = Point2Bundle.from_map(
        {"a": Point2.at(0, 0), "b": Point2.at(4, 0), "c": Point2.at(2, 6)}, roster=["a", "b", "c", "z"]
    )
    assert cloud.centroid().resolve().approx_equal(Point2Value.of(2, 2))  # z is absent, not counted


def test_where_narrows_roster_and_support() -> None:
    cloud = Point2Bundle.from_map({"a": Point2.at(1, 0), "b": Point2.at(0, 2), "c": Point2.at(5, 5)})
    sub = cloud.where(["a", "c"])
    assert set(sub.support().resolve().keys) == {"a", "c"}
    assert isinstance(sub.at("b").decide(), Unresolvable)


def test_transformed_by_broadcast() -> None:
    moved = _cloud().transformed_by(Transform2.translation((1, 2)))
    assert moved.at(0).resolve().approx_equal(Point2Value.of(1, 2))
    assert moved.at(1).resolve().approx_equal(Point2Value.of(5, 2))


def test_distance_to_is_key_aligned() -> None:
    a = Point2Bundle.from_array([[0, 0], [10, 0]])
    b = Point2Bundle.from_array([[3, 4], [10, 0]])
    dist = a.distance_to(b)
    assert dist.at(0).resolve() == 5.0
    assert dist.at(1).resolve() == 0.0


def test_distance_to_intersects_keys() -> None:
    masked = Point2Bundle.from_map({"a": Point2.at(0, 0)}, roster=["a", "b"])
    other = Point2Bundle.from_map({"a": Point2.at(3, 4)})
    assert masked.distance_to(other).at("a").resolve() == 5.0
    assert isinstance(masked.distance_to(other).at("b").decide(), Unresolvable)  # b absent → off the intersection


def test_relabel_is_the_identity_transfer() -> None:
    cloud = Point2Bundle.from_array([[0, 0], [4, 0]], keys=["m0", "m1"])
    relabeled = cloud.relabel(RosterMap.of({"m0": "j0", "m1": "j1"}))
    assert relabeled.at("j0").resolve().approx_equal(Point2Value.of(0, 0))
    assert isinstance(relabeled.at("m0").decide(), Unresolvable)  # old key gone


def test_construction_is_strict_on_a_detached_member() -> None:
    from fungeom import Frame2

    detached = Point2.at(1, 1, frame=Frame2.detached("loose"))
    decision = Point2Bundle.of([Point2.at(1, 1), detached]).decide()
    assert isinstance(decision, Unresolvable)


def test_malformed_construction() -> None:
    p = Point2.at(0, 0)
    assert "2 members for 1 keys" in Point2Bundle.of([p, p], keys=["a"]).decide().reason
    assert "duplicate keys" in Point2Bundle.of([p, p], keys=["a", "a"]).decide().reason


def test_in_frame_flattens_a_3d_cloud_into_a_plane() -> None:
    from fungeom import Direction3, Plane, Point3, Point3Bundle

    plane = Plane.through(Point3.at(0, 0, 3), Direction3.of(0, 0, 1))  # the z = 3 plane
    cloud = Point3Bundle.from_map({"a": Point3.at(0, 0, 3), "b": Point3.at(2, 0, 99)}, roster=["a", "b", "occ"])
    flat = cloud.in_frame(plane)
    assert isinstance(flat, Point2Bundle)
    # the in-plane part survives; the off-plane height (99) is dropped to the chart
    assert flat.at("a").resolve().approx_equal(Point2Value.of(0, 0))
    assert np.allclose(flat.at("b").resolve().coord, [0, -2])  # (2,0) flattened in this plane's gauge
    assert flat.count().resolve() == 2.0  # the occluded key stays absent
    assert flat.present("occ").resolve() is False
    # round-trip a flattened point back through embed lands on the plane
    world = plane.embed(flat.at("b")).resolve()
    assert np.isclose(world.coord[2], 3.0)


def test_empty_fold_is_unresolvable() -> None:
    decision = Point2Bundle.of([]).centroid().decide()
    assert isinstance(decision, Unresolvable)
    assert "empty bundle" in decision.reason
