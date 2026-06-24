"""Boundary — the off-domain reading policies."""

from __future__ import annotations

from fungeom import Boundary


def test_undefined() -> None:
    assert Boundary.undefined.outside(5.0, (0.0, 1.0)) is None


def test_hold() -> None:
    assert Boundary.hold.outside(5.0, (0.0, 1.0)) == 1.0  # clamps above
    assert Boundary.hold.outside(-3.0, (0.0, 1.0)) == 0.0  # clamps below
