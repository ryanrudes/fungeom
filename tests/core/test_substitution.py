"""Binding free-variable leaves: the structural ``bind`` / ``_substitute`` rewrite.

``bind(env)`` walks the immutable graph and swaps each free leaf for its bound resolver,
returning a *new* graph the ordinary ``decide`` / ``resolve`` machinery evaluates — and it
returns subgraphs with no (bound) frees **unchanged**, so concrete graphs bind to themselves
and DAG sharing survives. These tests exercise that generic core machinery directly (the
per-primitive ``Point3.free`` surface is tested in ``test_point3.py``; the end-to-end
acceptance in ``cross_cutting/test_free_variables.py``).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom import Point3, Resolvability, Resolvable, Resolver, Unresolvable, gather


def test_free_less_graph_binds_to_itself() -> None:
    concrete = Point3.at(0, 0, 0).midpoint(Point3.at(2, 4, 6))
    assert concrete.free_variables() == frozenset()
    assert concrete.bind({"anything": Point3.at(9, 9, 9)}) is concrete  # no frees -> identity, cache kept


def test_bind_substitutes_a_free_leaf_in_a_tuple_field() -> None:
    var = object()
    centroid = Point3.centroid([Point3.free(var), Point3.at(2, 0, 0), Point3.at(0, 2, 0)])
    assert centroid.free_variables() == frozenset((var,))
    assert isinstance(centroid.decide(), Unresolvable)  # unbound on its own
    bound = centroid.bind({var: Point3.at(2, 2, 0)})
    assert bound is not centroid  # the spine from the free leaf up was rebuilt
    assert bound.free_variables() == frozenset()
    assert tuple(centroid.resolve_in({var: Point3.at(2, 2, 0)}).coord) == (4 / 3, 4 / 3, 0)


def test_bind_preserves_dag_sharing_via_the_memo() -> None:
    var = object()
    shared = Point3.free(var)  # one leaf referenced in two positions
    graph = shared.midpoint(shared.translate((1, 0, 0)))  # both children reach the *same* free node
    bound = graph.bind({var: Point3.at(4, 0, 0)})
    bound_leaf, translated, _t = bound.children()  # Lerp3(a, b, t): a is the leaf, b wraps it
    # The shared free leaf was substituted exactly once, so both occurrences are the same object.
    assert translated.children()[0] is bound_leaf
    assert tuple(graph.resolve_in({var: Point3.at(4, 0, 0)}).coord) == (4.5, 0, 0)


def test_unbound_free_stays_free_after_binding_others() -> None:
    a, b = object(), object()
    graph = Point3.centroid([Point3.free(a), Point3.free(b)])
    partly = graph.bind({a: Point3.at(0, 0, 0)})
    assert partly.free_variables() == frozenset((b,))  # only b remains
    assert isinstance(partly.decide(), Unresolvable)


# --- the generic walk reaches a *list* field too (parity with children()) ----------------


@dataclass(frozen=True, eq=False)
class _ListNode(Resolver[list[object]]):
    """A toy resolver whose children live in a ``list`` field — no production resolver has one,
    so this is what exercises the list arm of the structural walk."""

    members: list[Point3]

    def _decide(self) -> Resolvability[list[object]]:
        return gather(member.decide() for member in self.members)


def test_substitute_walks_a_list_field() -> None:
    var = object()
    node = _ListNode(members=[Point3.free(var), Point3.at(1, 2, 3)])
    assert node.free_variables() == frozenset((var,))
    bound = node.bind({var: Point3.at(0, 0, 0)})
    assert isinstance(bound, _ListNode)
    assert isinstance(bound.members, list) and bound.members[1] is node.members[1]  # rebuilt as a list, concrete kept
    assert isinstance(bound.decide(), Resolvable)


def test_non_dataclass_resolver_binds_to_itself() -> None:
    class _Bare(Resolver[int]):
        def _decide(self) -> Resolvability[int]:
            return Resolvable(0)

    bare = _Bare()
    assert bare.free_variables() == frozenset()
    assert bare.bind({"x": Point3.at(0, 0, 0)}) is bare  # no __dataclass_fields__ -> unchanged
