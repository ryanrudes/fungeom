"""Point3Bundle — the first collection: a keyed, maskable point cloud."""

from __future__ import annotations

import numpy as np

from fungeom import CoordinateFrame, Point3, Point3Bundle, Unresolvable
from fungeom.values import BundleValue


def _cloud() -> Point3Bundle:
    return Point3Bundle.of([Point3.at(0, 0, 0), Point3.at(4, 0, 0), Point3.at(0, 3, 0)])


def test_positional_construction_and_at() -> None:
    cloud = _cloud()
    assert np.allclose(cloud.at(0).resolve().coord, [0, 0, 0])
    assert np.allclose(cloud.at(1).resolve().coord, [4, 0, 0])
    # at() bridges back to the static Point3 algebra
    assert cloud.at(0).distance_to(cloud.at(1)).resolve() == 4.0
    assert cloud.count().resolve() == 3.0


def test_from_array_construction() -> None:
    cloud = Point3Bundle.from_array([[0, 0, 0], [4, 0, 0], [0, 3, 0]])
    assert cloud.count().resolve() == 3.0
    assert np.allclose(cloud.at(1).resolve().coord, [4, 0, 0])
    assert np.allclose(cloud.centroid().resolve().coord, [4 / 3, 1, 0])
    keyed = Point3Bundle.from_array([[1, 0, 0], [0, 2, 0]], keys=["a", "b"])
    assert np.allclose(keyed.at("a").resolve().coord, [1, 0, 0])


def test_keyed_construction() -> None:
    cloud = Point3Bundle.from_map({"a": Point3.at(1, 0, 0), "b": Point3.at(0, 2, 0)})
    assert np.allclose(cloud.at("a").resolve().coord, [1, 0, 0])
    assert cloud.present("a").resolve() is True
    assert cloud.resolve().support() == ("a", "b")


def test_masking_via_a_wider_roster() -> None:
    # An occluded-marker frame: RWRIST is in the roster but absent this frame.
    cloud = Point3Bundle.from_map(
        {"HEAD": Point3.at(0, 0, 10), "LWRIST": Point3.at(-2, 0, 0)},
        roster=["HEAD", "LWRIST", "RWRIST"],
    )
    value = cloud.resolve()
    assert value.support() == ("HEAD", "LWRIST")
    assert value.count == 2
    assert repr(value) == "BundleValue(2 of 3 keys, 1 absent)"
    assert cloud.present("HEAD").resolve() is True
    assert cloud.present("RWRIST").resolve() is False
    assert cloud.count().resolve() == 2.0
    # absent vs unknown keys give distinct reasons
    assert "absent" in cloud.at("RWRIST").decide().reason
    assert "not in the bundle's roster" in cloud.at("NOPE").decide().reason


def test_centroid_folds_over_present_members() -> None:
    # masked centroid uses only the present members
    cloud = Point3Bundle.from_map(
        {"a": Point3.at(0, 0, 0), "b": Point3.at(2, 0, 0)},
        roster=["a", "b", "c"],
    )
    assert np.allclose(cloud.centroid().resolve().coord, [1, 0, 0])  # c absent, ignored
    assert np.allclose(_cloud().centroid().resolve().coord, [4 / 3, 1, 0])


def test_where_narrows_roster_and_support() -> None:
    cloud = Point3Bundle.from_map(
        {"HEAD": Point3.at(0, 0, 10), "LWRIST": Point3.at(-2, 0, 0)},
        roster=["HEAD", "LWRIST", "RWRIST"],
    )
    sub = cloud.where(["HEAD", "RWRIST"])  # keep one present + one absent key
    value = sub.resolve()
    assert value.roster == ("HEAD", "RWRIST")
    assert value.support() == ("HEAD",)
    assert sub.count().resolve() == 1.0


def test_full_bundle_repr_has_no_absent_suffix() -> None:
    assert repr(_cloud().resolve()) == "BundleValue(3 of 3 keys)"
    assert isinstance(_cloud().resolve(), BundleValue)


def test_construction_is_strict_on_a_detached_member() -> None:
    # A point on an ungrounded frame makes the whole bundle Unresolvable.
    bad = Point3.at(0, 0, 0, frame=CoordinateFrame.detached("loose"))
    decision = Point3Bundle.of([Point3.at(1, 1, 1), bad]).decide()
    assert isinstance(decision, Unresolvable)
    assert "not grounded" in decision.reason


def test_malformed_construction() -> None:
    p = Point3.at(0, 0, 0)
    assert "2 points for 1 keys" in Point3Bundle.of([p, p], keys=["a"]).decide().reason
    assert "duplicate keys" in Point3Bundle.of([p, p], keys=["a", "a"]).decide().reason


def test_empty_fold_is_unresolvable() -> None:
    decision = Point3Bundle.of([]).centroid().decide()
    assert isinstance(decision, Unresolvable)
    assert "empty bundle" in decision.reason
