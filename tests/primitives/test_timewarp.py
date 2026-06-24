"""TimeWarp — the monotonic, piecewise-linear content-warp algebra."""

from __future__ import annotations

from fungeom import TimeWarp, Unresolvable


def test_through_reconstructs_linearly_between_knots() -> None:
    w = TimeWarp.through([(0.0, 0.0), (1.0, 0.5), (2.0, 2.0)]).resolve()
    assert w.domain == (0.0, 2.0)
    assert w.apply(0.0) == 0.0
    assert w.apply(2.0) == 2.0
    assert w.apply(1.0) == 0.5
    assert w.apply(1.5) == 1.25  # halfway between (1, 0.5) and (2, 2.0)


def test_apply_clamps_at_the_knot_ends() -> None:
    w = TimeWarp.through([(0.0, 10.0), (1.0, 20.0)]).resolve()
    assert w.apply(-5.0) == 10.0  # at/below first knot
    assert w.apply(5.0) == 20.0  # at/above last knot


def test_inverse_swaps_the_correspondences() -> None:
    w = TimeWarp.through([(0.0, 0.0), (1.0, 0.5), (2.0, 2.0)])
    inv = w.inverse().resolve()
    assert inv.apply(1.25) == 1.5  # the inverse of apply(1.5) == 1.25
    assert inv.apply(0.5) == 1.0


def test_needs_at_least_two_knots() -> None:
    decision = TimeWarp.through([(0.0, 0.0)]).decide()
    assert isinstance(decision, Unresolvable)
    assert "at least two" in decision.reason


def test_source_must_be_strictly_increasing() -> None:
    decision = TimeWarp.through([(0.0, 0.0), (1.0, 5.0), (0.5, 2.0)]).decide()
    assert isinstance(decision, Unresolvable)
    assert "source times must be strictly increasing" in decision.reason


def test_target_must_be_strictly_increasing() -> None:
    # An order-preserving map cannot send two distinct source times to the same target.
    decision = TimeWarp.through([(0.0, 0.0), (1.0, 0.0)]).decide()
    assert isinstance(decision, Unresolvable)
    assert "target times must be strictly increasing" in decision.reason


def test_repr_names_knot_count_and_domain() -> None:
    w = TimeWarp.through([(0.0, 0.0), (2.0, 5.0)]).resolve()
    assert repr(w) == "PiecewiseLinearWarp(2 knots over (0.0, 2.0))"
