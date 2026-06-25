"""RosterMap — the entity-axis identity correspondence: of/identity, compose, inverse."""

from __future__ import annotations

from fungeom import Frame, Point3, Point3Bundle, Roster, RosterMap, Unresolvable
from fungeom.values import KeyCorrespondence, RosterValue


def test_of_builds_the_correspondence() -> None:
    m = RosterMap.of({"lwrist": "L_Hand", "rwrist": "R_Hand"}).resolve()
    assert m.maps("lwrist") and not m.maps("head")
    assert m.apply("lwrist") == "L_Hand"
    assert m.source_keys == ("lwrist", "rwrist")
    assert m.target_keys == ("L_Hand", "R_Hand")


def test_known_wraps_a_value() -> None:
    value = KeyCorrespondence({"a": "B"})
    assert RosterMap.known(value).resolve() == value


def test_source_and_target_are_rosters() -> None:
    m = RosterMap.of({"lwrist": "L_Hand", "rwrist": "R_Hand"})
    assert m.source().resolve() == RosterValue(("lwrist", "rwrist"))
    assert m.target().resolve() == RosterValue(("L_Hand", "R_Hand"))
    # the target image deduplicates: two sources, one shared target.
    # assert on the raw value (a tuple) so the dedup is pinned to KeyCorrespondence.target_keys
    # itself, not masked by RosterValue's own (order-free, set-equal) dedup downstream.
    assert RosterMap.of({"a": "Z", "b": "Z"}).resolve().target_keys == ("Z",)
    assert RosterMap.of({"a": "Z", "b": "Z"}).target().resolve() == RosterValue(("Z",))


def test_maps_predicate() -> None:
    m = RosterMap.of({"lwrist": "L_Hand"})
    assert m.maps("lwrist").resolve() is True
    assert m.maps("rwrist").resolve() is False


def test_identity_over_a_roster() -> None:
    # accepts a plain sequence ...
    m = RosterMap.identity(["a", "b", "c"]).resolve()
    assert m.pairs == {"a": "a", "b": "b", "c": "c"}
    # ... or a Roster resolver (e.g. a bundle's support)
    from_roster = RosterMap.identity(Roster.of(["x", "y"])).resolve()
    assert from_roster.pairs == {"x": "x", "y": "y"}


def test_inverse_swaps_source_and_target() -> None:
    m = RosterMap.of({"lwrist": "L_Hand", "rwrist": "R_Hand"})
    inv = m.inverse().resolve()
    assert inv.pairs == {"L_Hand": "lwrist", "R_Hand": "rwrist"}
    # round-trip: inverse ∘ map is the identity on the source domain
    assert (m.inverse() @ m).resolve().pairs == {"lwrist": "lwrist", "rwrist": "rwrist"}


def test_inverse_of_non_injective_is_unresolvable() -> None:
    # two sources sharing a target -> no inverse (the entity-axis analog of a zero-rate clock)
    decision = RosterMap.of({"a": "Z", "b": "Z"}).inverse().decide()
    assert isinstance(decision, Unresolvable)
    assert "non-injective" in decision.reason


def test_compose_chains_through_shared_keys() -> None:
    # inner: marker -> mid, outer: mid -> joint  =>  outer ∘ inner: marker -> joint
    inner = RosterMap.of({"m1": "mid1", "m2": "mid2"})
    outer = RosterMap.of({"mid1": "joint1"})  # mid2 not in outer's domain
    composed = (outer @ inner).resolve()
    # total, but narrows to the keys that chain all the way through
    assert composed.pairs == {"m1": "joint1"}


def test_compose_with_no_shared_keys_is_empty() -> None:
    composed = (RosterMap.of({"x": "y"}) @ RosterMap.of({"a": "b"})).resolve()
    assert composed.pairs == {}


def test_value_equality_and_repr() -> None:
    assert KeyCorrespondence({"a": "B"}) == KeyCorrespondence({"a": "B"})
    assert KeyCorrespondence({"a": "B"}) != KeyCorrespondence({"a": "C"})
    assert KeyCorrespondence({"a": "B"}) != "a:B"  # cross-type inequality
    assert hash(KeyCorrespondence({"a": "B"})) == hash(KeyCorrespondence({"a": "B"}))
    assert repr(KeyCorrespondence({"a": "B", "c": "D"})) == "KeyCorrespondence(2 pairs)"


def test_relabel_a_point_cloud_is_the_identity_transfer() -> None:
    # the retarget seam: a source-keyed cloud carried onto target keys
    cloud = Point3Bundle.from_map({"lwrist": Point3.at(1, 0, 0), "rwrist": Point3.at(0, 1, 0)})
    m = RosterMap.of({"lwrist": "L_Hand", "rwrist": "R_Hand"})
    transferred = cloud.relabel(m)
    value = transferred.resolve()
    assert value.roster == ("L_Hand", "R_Hand")
    assert transferred.at("L_Hand").resolve().coord.tolist() == [1.0, 0.0, 0.0]
    assert transferred.at("R_Hand").resolve().coord.tolist() == [0.0, 1.0, 0.0]


def test_relabel_transfers_the_occlusion_mask() -> None:
    # an absent source key stays absent under its target name; the mask survives the rename
    cloud = Point3Bundle.from_map({"lwrist": Point3.at(1, 0, 0)}, roster=["lwrist", "rwrist"])
    m = RosterMap.of({"lwrist": "L_Hand", "rwrist": "R_Hand"})
    value = cloud.relabel(m).resolve()
    assert value.roster == ("L_Hand", "R_Hand")  # both declared
    assert value.support() == ("L_Hand",)  # only the present one carries through


def test_relabel_drops_keys_outside_the_domain() -> None:
    cloud = Point3Bundle.from_map({"lwrist": Point3.at(1, 0, 0), "rwrist": Point3.at(0, 1, 0)})
    partial = RosterMap.of({"lwrist": "L_Hand"})  # rwrist unmapped
    value = cloud.relabel(partial).resolve()
    assert value.roster == ("L_Hand",)
    assert value.support() == ("L_Hand",)


def test_relabel_collision_is_unresolvable() -> None:
    # a correspondence that collapses two present keys onto one target destroys the collection
    cloud = Point3Bundle.from_map({"a": Point3.at(0, 0, 0), "b": Point3.at(1, 1, 1)})
    decision = cloud.relabel(RosterMap.of({"a": "Z", "b": "Z"})).decide()
    assert isinstance(decision, Unresolvable)
    assert "collapses" in decision.reason


def test_relabel_collision_among_declared_keys_is_unresolvable() -> None:
    # even when one of the colliding keys is absent, the target roster would duplicate -> Unresolvable
    cloud = Point3Bundle.from_map({"a": Point3.at(0, 0, 0)}, roster=["a", "b"])
    decision = cloud.relabel(RosterMap.of({"a": "Z", "b": "Z"})).decide()
    assert isinstance(decision, Unresolvable)


def test_relabel_works_across_every_facade() -> None:
    from fungeom import (
        Direction3,
        Direction3Bundle,
        Scalar,
        ScalarBundle,
        Transform,
        TransformBundle,
        Vec3,
        Vec3Bundle,
    )

    m = RosterMap.of({0: "a", 1: "b"})
    assert ScalarBundle.of([Scalar.of(1), Scalar.of(2)]).relabel(m).at("b").resolve() == 2.0
    assert Vec3Bundle.of([Vec3.of(1, 0, 0), Vec3.of(0, 1, 0)]).relabel(m).at("a").resolve().tolist() == [1, 0, 0]
    d = Direction3Bundle.of([Direction3.of(1, 0, 0), Direction3.of(0, 1, 0)]).relabel(m)
    assert d.at("b").resolve().vector.tolist() == [0, 1, 0]
    t = TransformBundle.of([Transform.identity(), Transform.identity()]).relabel(m)
    assert t.present("a").resolve() is True


def test_unresolvable_rostermap_propagates() -> None:
    # a roster map is Unresolvable only by propagation — e.g. identity over an unbuildable support
    bad_support = Point3Bundle.of([Point3.at(0, 0, 0, frame=Frame.detached("loose"))]).support()
    bad_map = RosterMap.identity(bad_support)
    assert isinstance(bad_map.decide(), Unresolvable)
    assert isinstance(bad_map.inverse().decide(), Unresolvable)
    assert isinstance(bad_map.source().decide(), Unresolvable)
    assert isinstance(bad_map.target().decide(), Unresolvable)
    assert isinstance(bad_map.maps("x").decide(), Unresolvable)
    assert isinstance((bad_map @ RosterMap.identity(["x"])).decide(), Unresolvable)
