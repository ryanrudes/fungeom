"""Roster — the entity-axis support set: key-set algebra, membership, cardinality."""

from __future__ import annotations

from fungeom import Frame, Point3, Point3Bundle, Roster, Unresolvable
from fungeom.values import RosterValue


def test_of_dedups_and_keeps_first_seen_order() -> None:
    roster = Roster.of(["lwrist", "rwrist", "lwrist", "head"]).resolve()
    assert roster.keys == ("lwrist", "rwrist", "head")
    assert len(roster) == 3
    assert "head" in roster and "foot" not in roster
    assert list(roster) == ["lwrist", "rwrist", "head"]  # iterable over its keys, in order
    assert Roster.empty.resolve().is_empty


def test_value_equality_is_order_free() -> None:
    # a roster is a set, not a sequence: equal keys compare equal regardless of order
    assert RosterValue(("a", "b", "c")) == RosterValue(("c", "a", "b"))
    assert hash(RosterValue(("a", "b"))) == hash(RosterValue(("b", "a")))
    assert RosterValue(("a", "b")) != RosterValue(("a", "c"))
    assert RosterValue(("a",)) != "a"  # cross-type inequality


def test_union() -> None:
    a = Roster.of(["x", "y", "z"])
    b = Roster.of(["y", "z", "w"])
    # union keeps this roster's keys first, then the new ones; order-free equality holds
    assert a.union(b).resolve() == RosterValue(("x", "y", "z", "w"))
    assert a.union(b).resolve().keys == ("x", "y", "z", "w")


def test_intersection() -> None:
    # operands whose orders differ, so the documented "this roster's order" is load-bearing:
    # iterating the *other* roster would give ("y", "z") — assert .keys to kill that mutation
    a = Roster.of(["z", "y", "x"])
    b = Roster.of(["y", "z", "w"])
    assert a.intersection(b).resolve().keys == ("z", "y")  # self's order, not other's
    assert a.intersection(b).resolve() == RosterValue(("z", "y"))
    # no shared keys -> empty (total, not Unresolvable)
    assert Roster.of(["x"]).intersection(Roster.of(["q"])).resolve().is_empty


def test_difference() -> None:
    # multi-key result, ordered by self: pins "this roster's order" for difference too
    a = Roster.of(["z", "y", "x", "w"])
    b = Roster.of(["y"])
    assert a.difference(b).resolve().keys == ("z", "x", "w")
    assert a.difference(b).resolve() == RosterValue(("z", "x", "w"))
    # subtracting a superset is empty
    assert a.difference(Roster.of(["z", "y", "x", "w", "extra"])).resolve().is_empty


def test_count_is_cardinality() -> None:
    assert Roster.of(["a", "b", "c"]).count().resolve() == 3.0
    assert Roster.empty.count().resolve() == 0.0
    # a fold over the algebra: |A ∪ B|
    assert Roster.of(["a", "b"]).union(Roster.of(["b", "c"])).count().resolve() == 3.0


def test_contains() -> None:
    roster = Roster.of(["lwrist", "rwrist"])
    assert roster.contains("lwrist").resolve() is True
    assert roster.contains("head").resolve() is False
    assert Roster.empty.contains("anything").resolve() is False


def test_repr() -> None:
    assert repr(Roster.of(["a", "b"]).resolve()) == "RosterValue({'a', 'b'})"
    assert repr(Roster.empty.resolve()) == "RosterValue({})"


def test_support_of_a_bundle_is_a_roster() -> None:
    # the rung-3 upgrade: a bundle's present keys lift to a Roster, composable with the algebra
    cloud = Point3Bundle.from_map({"lwrist": Point3.at(1, 0, 0)}, roster=["lwrist", "rwrist"])
    support = cloud.support()
    assert support.resolve() == RosterValue(("lwrist",))  # rwrist absent -> off the support
    assert support.contains("lwrist").resolve() is True
    assert support.contains("rwrist").resolve() is False
    assert support.count().resolve() == 1.0


def test_unresolvable_roster_propagates_through_the_algebra() -> None:
    # a roster is only Unresolvable by propagation — e.g. the support of an unbuildable bundle
    bad = Point3Bundle.of([Point3.at(0, 0, 0, frame=Frame.detached("loose"))]).support()
    assert isinstance(bad.decide(), Unresolvable)
    assert isinstance(bad.union(Roster.of(["x"])).decide(), Unresolvable)
    assert isinstance(bad.count().decide(), Unresolvable)
    assert isinstance(bad.contains("x").decide(), Unresolvable)
