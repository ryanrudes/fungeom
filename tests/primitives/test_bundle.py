"""Point3Bundle — the first collection: a keyed, maskable point cloud."""

from __future__ import annotations

import numpy as np

from fungeom import (
    CoordinateFrame,
    Direction3,
    Direction3Bundle,
    Point3,
    Point3Bundle,
    Scalar,
    ScalarBundle,
    Transform,
    TransformBundle,
    Unresolvable,
    Vec3,
    Vec3Bundle,
)
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
    assert "2 members for 1 keys" in Point3Bundle.of([p, p], keys=["a"]).decide().reason
    assert "duplicate keys" in Point3Bundle.of([p, p], keys=["a", "a"]).decide().reason


def test_empty_fold_is_unresolvable() -> None:
    decision = Point3Bundle.of([]).centroid().decide()
    assert isinstance(decision, Unresolvable)
    assert "empty bundle" in decision.reason


def test_fit_plane() -> None:
    # a slightly-noisy planar (z ≈ 0) cloud fits a plane with a ±z normal through the points
    cloud = Point3Bundle.from_array([[0, 0, 0], [2, 0, 0.01], [0, 3, -0.01], [2, 3, 0], [1, 1, 0.005]])
    plane = cloud.fit_plane()
    assert np.allclose(np.abs(plane.normal().resolve().vector), [0, 0, 1], atol=0.02)
    assert abs(plane.signed_distance(Point3.at(1, 1, 0)).resolve()) < 0.02  # the points are near the plane
    # the fitted sign is arbitrary; facing resolves it
    assert plane.facing(Point3.at(0, 0, 10)).normal().resolve().vector[2] > 0


def test_fit_plane_degeneracy() -> None:
    assert "at least three" in Point3Bundle.from_array([[0, 0, 0], [1, 0, 0]]).fit_plane().decide().reason
    # collinear (rod-like): no unique least-variance direction
    collinear = Point3Bundle.from_array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]).fit_plane()
    assert isinstance(collinear.decide(), Unresolvable)
    assert "no unique normal" in collinear.decide().reason
    # isotropic (ball-like — a cube's 8 corners): the gap test catches it where σ₂>0 would not
    cube = [[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    assert isinstance(Point3Bundle.from_array(cube).fit_plane().decide(), Unresolvable)


def test_vec3_bundle() -> None:
    cloud = Vec3Bundle.from_array([[1, 0, 0], [3, 0, 0]])
    assert np.allclose(cloud.at(1).resolve(), [3, 0, 0])
    assert np.allclose(cloud.mean().resolve(), [2, 0, 0])  # total
    assert cloud.count().resolve() == 2.0
    # keyed + masking works on every facade (shared core)
    masked = Vec3Bundle.from_map({"x": Vec3.of(1, 0, 0)}, roster=["x", "y"])
    assert masked.present("y").resolve() is False
    assert "absent" in masked.at("y").decide().reason
    assert np.allclose(masked.where(["x"]).mean().resolve(), [1, 0, 0])
    assert isinstance(Vec3Bundle.of([]).mean().decide(), Unresolvable)  # empty fold


def test_scalar_bundle() -> None:
    cloud = ScalarBundle.from_array([1.0, 2.0, 6.0])
    assert cloud.at(2).resolve() == 6.0
    assert cloud.mean().resolve() == 3.0
    keyed = ScalarBundle.from_map({"a": Scalar.of(10.0), "b": Scalar.of(20.0)})
    assert keyed.mean().resolve() == 15.0
    assert isinstance(ScalarBundle.of([]).mean().decide(), Unresolvable)


def test_direction3_bundle_mean_and_partiality() -> None:
    cloud = Direction3Bundle.from_array([[1, 0, 0], [0, 1, 0]])
    assert np.allclose(cloud.at(0).resolve().vector, [1, 0, 0])
    assert np.allclose(cloud.mean().resolve().vector, [2**-0.5, 2**-0.5, 0])  # normalize the sum
    # a zero-vector member makes the whole bundle Unresolvable (strict build)
    assert isinstance(Direction3Bundle.from_array([[0, 0, 0]]).decide(), Unresolvable)
    # antipodal directions cancel: their mean has no direction
    cancel = Direction3Bundle.from_array([[1, 0, 0], [-1, 0, 0]]).mean().decide()
    assert isinstance(cancel, Unresolvable)
    assert "cancel" in cancel.reason
    assert isinstance(Direction3Bundle.of([]).mean().decide(), Unresolvable)  # empty fold
    keyed = Direction3Bundle.from_map({"x": Direction3.of(1, 0, 0)}, roster=["x", "y"])
    assert keyed.present("y").resolve() is False


def test_transform_bundle() -> None:
    cloud = TransformBundle.of([Transform.identity(), Transform.identity()], keys=["a", "b"])
    assert cloud.count().resolve() == 2.0
    assert np.allclose(cloud.at("a").resolve().translation, [0, 0, 0])
    assert cloud.where(["a"]).count().resolve() == 1.0
    assert "not in the bundle's roster" in cloud.where(["a"]).at("b").decide().reason  # b dropped
    keyed = TransformBundle.from_map({"a": Transform.identity()}, roster=["a", "b"])
    assert keyed.present("b").resolve() is False
    assert "absent" in keyed.at("b").decide().reason  # b in roster but masked


def test_scalar_bundle_algebra() -> None:
    a = ScalarBundle.from_map({"x": Scalar.of(10.0), "y": Scalar.of(20.0)})
    b = ScalarBundle.from_map({"y": Scalar.of(2.0), "z": Scalar.of(9.0)})  # overlaps on y only
    assert (a + b).resolve().support() == ("y",)  # zip on the key intersection
    assert (a + b).at("y").resolve() == 22.0
    assert (a - b).at("y").resolve() == 18.0
    assert (a * b).at("y").resolve() == 40.0
    assert (a / b).at("y").resolve() == 10.0
    # static partiality flows through: ÷0 at a key is Unresolvable
    div0 = a / ScalarBundle.from_map({"x": Scalar.of(0.0)})
    assert isinstance(div0.at("x").decide(), Unresolvable)
    # disjoint keys → a valid empty bundle
    disjoint = ScalarBundle.of([Scalar.of(1.0)], keys=["a"]) + ScalarBundle.of([Scalar.of(2.0)], keys=["b"])
    assert disjoint.count().resolve() == 0.0
    # sum is total (identity 0 over empty); mean is not
    assert a.sum().resolve() == 30.0
    assert ScalarBundle.of([]).sum().resolve() == 0.0


def test_vec3_bundle_algebra() -> None:
    u = Vec3Bundle.from_array([[1, 0, 0], [0, 1, 0]])
    v = Vec3Bundle.from_array([[1, 0, 0], [1, 0, 0]])
    assert np.allclose((u + v).at(0).resolve(), [2, 0, 0])
    assert np.allclose((u - v).at(1).resolve(), [-1, 1, 0])
    assert u.dot(v).at(0).resolve() == 1.0  # cross-type lift → ScalarBundle
    assert u.dot(v).at(1).resolve() == 0.0
    assert np.allclose(u.sum().resolve(), [1, 1, 0])
    assert np.allclose(Vec3Bundle.of([]).sum().resolve(), [0, 0, 0])  # zero vector over empty


def test_point3_bundle_algebra() -> None:
    p = Point3Bundle.from_array([[0, 0, 0], [0, 0, 0]])
    q = Point3Bundle.from_array([[3, 4, 0], [0, 0, 0]])
    assert p.distance_to(q).at(0).resolve() == 5.0  # cross-type lift → ScalarBundle
    assert np.allclose(p.displacement_to(q).at(0).resolve(), [3, 4, 0])  # → Vec3Bundle
    # broadcast one transform over the whole cloud (a map; preserves roster)
    moved = p.transformed_by(Transform.translation(Vec3.of(1, 2, 3)))
    assert np.allclose(moved.at(0).resolve().coord, [1, 2, 3])
    assert moved.count().resolve() == 2.0
    # broadcast preserves the roster: an absent key stays absent (distinguishes map from zip)
    occluded = Point3Bundle.from_map({"a": Point3.at(0, 0, 0)}, roster=["a", "b"])
    shifted = occluded.transformed_by(Transform.translation(Vec3.of(1, 0, 0)))
    assert shifted.resolve().roster == ("a", "b")  # full roster carried through
    assert shifted.resolve().support() == ("a",)  # b still absent, not collapsed
    assert shifted.present("b").resolve() is False
    # a cross-type zip also intersects keys
    masked = Point3Bundle.from_map({"a": Point3.at(0, 0, 0)}, roster=["a", "b"])
    other = Point3Bundle.from_map({"a": Point3.at(1, 0, 0)})
    assert masked.distance_to(other).resolve().support() == ("a",)
