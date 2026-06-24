"""Instant — affine construction, order, and affine reductions."""

from __future__ import annotations

import pytest

from fungeom import Duration, Instant, Scalar, Unresolvable
from fungeom.primitives.instant.resolvers.literal import as_instant_resolver


def test_at_and_epoch() -> None:
    assert Instant.at(5.0).resolve() == 5.0
    assert Instant.epoch.resolve() == 0.0
    assert Instant.at(Scalar.of(3.0)).resolve() == 3.0  # deferred scalar time


def test_as_instant_resolver_coercion() -> None:
    assert as_instant_resolver(7.0).resolve() == 7.0  # bare seconds lifted
    t = Instant.at(2.0)
    assert as_instant_resolver(t) is t  # an existing Instant is passed through


def test_shift_and_operators() -> None:
    t = Instant.at(10.0)
    assert t.shifted_by(Duration.of(5.0)).resolve() == 15.0
    assert t.shifted_by(2.0).resolve() == 12.0  # bare seconds
    assert (t + Duration.of(5.0)).resolve() == 15.0
    assert (t - Duration.of(4.0)).resolve() == 6.0  # Instant - Duration -> Instant


def test_difference_to_duration() -> None:
    later, earlier = Instant.at(10.0), Instant.at(3.0)
    assert earlier.duration_to(later).resolve() == 7.0
    diff = later - earlier  # Instant - Instant -> Duration
    assert isinstance(diff, Duration)
    assert diff.resolve() == 7.0


def test_lerp_and_midpoint() -> None:
    a, b = Instant.at(0.0), Instant.at(10.0)
    assert a.lerp(b, 0.25).resolve() == 2.5
    assert a.midpoint(b).resolve() == 5.0


def test_min_and_max() -> None:
    a, b = Instant.at(3.0), Instant.at(8.0)
    assert a.min(b).resolve() == 3.0
    assert a.max(b).resolve() == 8.0
    assert Instant.at(-2.0).min(a).resolve() == -2.0


def test_centroid_and_affine() -> None:
    pts = [Instant.at(0.0), Instant.at(4.0), Instant.at(8.0)]
    assert Instant.centroid(pts).resolve() == 4.0
    # affine generalizes lerp/centroid; weights need not sum to one (they normalize)
    assert Instant.affine([Instant.at(0.0), Instant.at(10.0)], [3.0, 1.0]).resolve() == 2.5
    assert Instant.affine(pts, [1.0, 1.0, 2.0]).resolve() == 5.0


def test_partialities() -> None:
    assert isinstance(Instant.centroid([]).decide(), Unresolvable)
    assert isinstance(Instant.affine([], []).decide(), Unresolvable)
    assert isinstance(Instant.affine([Instant.at(1.0), Instant.at(2.0)], [1.0, -1.0]).decide(), Unresolvable)
    with pytest.raises(ValueError):
        Instant.affine([Instant.at(1.0)], [1.0, 2.0])  # mismatched lengths


def test_before_and_after() -> None:
    early, late = Instant.at(1.0), Instant.at(5.0)
    assert early.before(late).resolve() is True
    assert early.after(late).resolve() is False
    assert late.after(early).resolve() is True
    assert early.before(early).resolve() is False  # strict
