"""Timeline — clocks, grounding, and instants placed upon them (mirrors Frame)."""

from __future__ import annotations

import pytest

from fungeom import MASTER_CLOCK, Duration, TimeMap, Timeline, Unresolvable
from fungeom.values import AffineTimeMap, Clock


def test_master_resolves_to_itself() -> None:
    assert Timeline.master.resolve() is MASTER_CLOCK


def test_derive_and_at() -> None:
    # a camera clock offset 10s after the master, sampled at local t=5 -> master 15
    camera = Timeline.master.derive("camera", TimeMap.shift(Duration.of(10.0)))
    assert camera.at(5.0).resolve() == 15.0
    # a half-speed clock: local t=3 -> master 6
    slow = Timeline.master.derive("slow", TimeMap.rate(2.0))
    assert slow.at(3.0).resolve() == 6.0


def test_nested_derive_composes_to_master() -> None:
    # master -> (shift 10) -> a -> (rate 2) -> b ;  local t=3 on b -> 10 + 2*3 = 16
    a = Timeline.master.derive("a", TimeMap.shift(Duration.of(10.0)))
    b = a.derive("b", TimeMap.rate(2.0))
    assert b.at(3.0).resolve() == 16.0


def test_to_master_and_relative_to() -> None:
    # camera = master shifted +10s; its map to master is (offset 10, rate 1)
    camera = Timeline.master.derive("camera", TimeMap.shift(Duration.of(10.0)))
    assert camera.to_master().resolve().approx_equal(AffineTimeMap(10.0, 1.0))
    assert Timeline.master.to_master().resolve().approx_equal(AffineTimeMap.identity())
    # relative_to: re-express camera seconds in a half-speed clock's seconds
    slow = Timeline.master.derive("slow", TimeMap.rate(2.0))
    # camera local t -> master (t + 10) -> slow ((t + 10) / 2)
    rel = camera.relative_to(slow).resolve()
    assert rel.approx_equal(AffineTimeMap(5.0, 0.5))
    assert rel.apply(0.0) == 5.0  # camera t=0 -> master 10 -> slow 5


def test_to_master_partialities() -> None:
    assert isinstance(Timeline.detached("loose").to_master().decide(), Unresolvable)
    # either side ungrounded makes relative_to undefined
    grounded = Timeline.master.derive("cam", TimeMap.shift(Duration.of(1.0)))
    assert isinstance(grounded.relative_to(Timeline.detached("loose")).decide(), Unresolvable)
    assert isinstance(Timeline.detached("loose").relative_to(grounded).decide(), Unresolvable)
    # a frozen (zero-rate) reference clock cannot be inverted into
    frozen = Timeline.master.derive("frozen", TimeMap.rate(0.0))
    decision = grounded.relative_to(frozen).decide()
    assert isinstance(decision, Unresolvable)
    assert "frozen" in decision.reason


def test_detached_timeline_is_unresolvable() -> None:
    loose = Timeline.detached("vicon")
    assert isinstance(loose.decide(), Unresolvable)
    decision = loose.at(5.0).decide()  # an instant on an un-synced clock has no master meaning
    assert isinstance(decision, Unresolvable)
    assert "master clock" in decision.reason


def test_known_wraps_a_grounded_clock() -> None:
    child = MASTER_CLOCK.child("cam", AffineTimeMap(10.0, 1.0))
    assert Timeline.known(child).at(0.0).resolve() == 10.0


def test_clock_value() -> None:
    # to_master composes a multi-level chain of raw clock values
    a = MASTER_CLOCK.child("a", AffineTimeMap(10.0, 1.0))
    b = a.child("b", AffineTimeMap(0.0, 2.0))
    assert b.to_master().approx_equal(AffineTimeMap(10.0, 2.0))
    assert b.is_grounded
    assert not Clock.detached("x").is_grounded
    assert repr(MASTER_CLOCK) == "Clock(name='master', parent=None)"
    assert repr(a) == "Clock(name='a', parent='master')"
    with pytest.raises(ValueError, match="not grounded"):
        Clock.detached("x").grounded()
