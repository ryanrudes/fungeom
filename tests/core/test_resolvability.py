"""The decidability evidence types: Resolvable / Unresolvable / gather."""

from __future__ import annotations

import pytest

from fungeom import Resolvable, Unresolvable, UnresolvableError, gather


def test_resolvable_carries_and_unwraps_its_value() -> None:
    r = Resolvable(42)
    assert r.ok is True
    assert r.value == 42
    assert r.unwrap() == 42


def test_unresolvable_carries_a_reason_and_raises_on_unwrap() -> None:
    u = Unresolvable("nope")
    assert u.ok is False
    assert u.reason == "nope"
    with pytest.raises(UnresolvableError, match="nope"):
        u.unwrap()


def test_gather_collects_all_values() -> None:
    result = gather([Resolvable(1), Resolvable(2), Resolvable(3)])
    assert isinstance(result, Resolvable)
    assert result.value == [1, 2, 3]


def test_gather_short_circuits_on_first_failure() -> None:
    result = gather([Resolvable(1), Unresolvable("first"), Unresolvable("second")])
    assert isinstance(result, Unresolvable)
    assert result.reason == "first"


def test_gather_of_empty_is_resolvable_empty() -> None:
    result = gather([])
    assert isinstance(result, Resolvable)
    assert result.value == []
