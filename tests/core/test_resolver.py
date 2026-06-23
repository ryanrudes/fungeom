"""The Resolver protocol: decide / resolve / is_resolvable / children / memoization."""

from __future__ import annotations

import pytest

from fungeom import Point3, Resolvable, Scalar, Unresolvable, UnresolvableError, Vec3


def test_resolve_and_is_resolvable_derive_from_decide() -> None:
    p = Point3.at(1, 2, 3)
    decision = p.decide()
    assert isinstance(decision, Resolvable)
    assert p.is_resolvable is True
    import numpy as np

    assert np.allclose(p.resolve().coord, [1, 2, 3])


def test_resolve_raises_when_unresolvable(bad: object) -> None:
    point = bad.point3  # type: ignore[attr-defined]
    assert isinstance(point.decide(), Unresolvable)
    assert point.is_resolvable is False
    with pytest.raises(UnresolvableError):
        point.resolve()


def test_decide_is_memoized() -> None:
    p = Point3.at(0, 0, 0).midpoint(Point3.at(2, 4, 6))
    assert p.decide() is p.decide()  # same evidence object — cached, not recomputed


def test_children_exposes_immediate_sub_resolvers() -> None:
    a, b = Point3.at(0, 0, 0), Point3.at(2, 2, 2)
    mid = a.midpoint(b)  # Lerp3(a, b, Scalar) — the parameter is itself a node
    first, second, t = mid.children()
    assert (first, second) == (a, b)
    assert t.resolve() == 0.5


def test_children_walks_tuple_and_list_fields() -> None:
    a, b = Point3.at(0, 0, 0), Point3.at(1, 1, 1)
    assert Point3.centroid([a, b]).children() == [a, b]  # tuple field


def test_leaf_resolver_has_no_children() -> None:
    assert Vec3.of(1, 2, 3).children() == []
    assert Scalar.of(1.0).children() == []


def test_non_dataclass_resolver_has_no_children() -> None:
    from fungeom import Resolvability, Resolvable, Resolver

    class Bare(Resolver[int]):
        def _decide(self) -> Resolvability[int]:
            return Resolvable(0)

    assert Bare().children() == []  # no __dataclass_fields__ -> empty
