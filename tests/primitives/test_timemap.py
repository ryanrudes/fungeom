"""TimeMap — the affine clock-map algebra (mirrors Transform)."""

from __future__ import annotations

import pytest

from fungeom import Duration, TimeMap, Unresolvable
from fungeom.values import AffineTimeMap


def test_constructors() -> None:
    assert TimeMap.identity().resolve() == AffineTimeMap(0.0, 1.0)
    assert TimeMap.shift(Duration.of(5.0)).resolve() == AffineTimeMap(5.0, 1.0)
    assert TimeMap.shift(2.0).resolve() == AffineTimeMap(2.0, 1.0)  # bare seconds
    assert TimeMap.rate(2.0).resolve() == AffineTimeMap(0.0, 2.0)
    assert TimeMap.affine(3.0, 2.0).resolve() == AffineTimeMap(3.0, 2.0)
    assert TimeMap.known(AffineTimeMap(1.0, 4.0)).resolve() == AffineTimeMap(1.0, 4.0)


def test_apply() -> None:
    assert AffineTimeMap(3.0, 2.0).apply(4.0) == 11.0  # 3 + 2*4


def test_aligning_recovers_offset() -> None:
    # One landmark fixes the offset only; the rate stays unity.
    m = TimeMap.aligning(2.0, 5.0).resolve()  # source 2 ↦ target 5
    assert m == AffineTimeMap(3.0, 1.0)
    assert m.apply(2.0) == 5.0


def test_through_recovers_offset_and_rate() -> None:
    # Two landmarks fix both offset and rate (drift) — clapper at start and end.
    m = TimeMap.through((0.0, 5.0), (10.0, 25.0)).resolve()
    assert m == AffineTimeMap(5.0, 2.0)  # rate (25-5)/(10-0)=2, offset 5
    assert m.apply(0.0) == 5.0
    assert m.apply(10.0) == 25.0


def test_through_is_unresolvable_when_sources_coincide() -> None:
    # A single source time leaves the rate undetermined.
    decision = TimeMap.through((3.0, 1.0), (3.0, 9.0)).decide()
    assert isinstance(decision, Unresolvable)
    assert "source time" in decision.reason


def test_compose() -> None:
    a, b = TimeMap.affine(1.0, 2.0), TimeMap.affine(3.0, 4.0)
    composed = (a @ b).resolve()  # apply b first, then a
    assert composed == AffineTimeMap(7.0, 8.0)  # offset 1+2*3, rate 2*4
    assert composed.apply(1.0) == a.resolve().apply(b.resolve().apply(1.0))


def test_inverse() -> None:
    inv = TimeMap.affine(6.0, 2.0).inverse().resolve()
    assert inv == AffineTimeMap(-3.0, 0.5)
    assert inv.apply(AffineTimeMap(6.0, 2.0).apply(4.0)) == pytest.approx(4.0)


def test_inverse_of_zero_rate_is_unresolvable() -> None:
    decision = TimeMap.rate(0.0).inverse().decide()
    assert isinstance(decision, Unresolvable)
    assert "invertible" in decision.reason


def test_value_helpers() -> None:
    assert AffineTimeMap(1.0, 2.0).approx_equal(AffineTimeMap(1.0, 2.0 + 1e-12))
    assert not AffineTimeMap(1.0, 2.0).approx_equal(AffineTimeMap(1.0, 3.0))
    assert AffineTimeMap(2.0, 1.0).is_invertible
    assert not AffineTimeMap(2.0, 0.0).is_invertible
    assert repr(AffineTimeMap(1.5, 2.0)) == "AffineTimeMap(offset=1.5, rate=2)"
