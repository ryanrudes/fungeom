"""Interval — construction, span queries, and the order-structured set algebra."""

from __future__ import annotations

import pytest

from fungeom import Duration, Instant, Interval, Unresolvable
from fungeom.values import IntervalValue


def test_between_and_span_queries() -> None:
    span = Interval.between(Instant.at(2.0), Instant.at(7.0))
    value = span.resolve()
    assert (value.start, value.end) == (2.0, 7.0)
    assert span.start().resolve() == 2.0
    assert span.end().resolve() == 7.0
    assert span.duration().resolve() == 5.0
    assert span.midpoint().resolve() == 4.5
    assert span.lerp(0.2).resolve() == 3.0


def test_constructors() -> None:
    assert Interval.of(Instant.at(1.0), Duration.of(3.0)).resolve() == IntervalValue(1.0, 4.0)
    assert Interval.point(Instant.at(5.0)).resolve() == IntervalValue(5.0, 5.0)
    assert Interval.around(Instant.at(10.0), Duration.of(2.0)).resolve() == IntervalValue(8.0, 12.0)


def test_clamp() -> None:
    span = Interval.between(Instant.at(0.0), Instant.at(10.0))
    assert span.clamp(Instant.at(-3.0)).resolve() == 0.0  # below
    assert span.clamp(4.0).resolve() == 4.0  # inside (bare seconds)
    assert span.clamp(Instant.at(99.0)).resolve() == 10.0  # above


def test_intersection_and_hull() -> None:
    a = Interval.between(Instant.at(0.0), Instant.at(6.0))
    b = Interval.between(Instant.at(4.0), Instant.at(10.0))
    assert a.intersection(b).resolve() == IntervalValue(4.0, 6.0)
    assert a.hull(b).resolve() == IntervalValue(0.0, 10.0)
    # closed intervals that touch at a single instant meet in that degenerate point
    touching = Interval.between(Instant.at(0.0), Instant.at(1.0))
    assert touching.intersection(Interval.between(Instant.at(1.0), Instant.at(2.0))).resolve() == (
        IntervalValue(1.0, 1.0)
    )


def test_shifted_and_expanded() -> None:
    span = Interval.between(Instant.at(2.0), Instant.at(8.0))
    assert span.shifted(Duration.of(3.0)).resolve() == IntervalValue(5.0, 11.0)
    assert span.shifted(-2.0).resolve() == IntervalValue(0.0, 6.0)  # bare seconds, earlier
    assert span.expanded(Duration.of(1.0)).resolve() == IntervalValue(1.0, 9.0)  # grow each end
    assert span.expanded(-1.0).resolve() == IntervalValue(3.0, 7.0)  # shrink each end


def test_partiality() -> None:
    assert not Interval.between(Instant.at(5.0), Instant.at(0.0)).is_resolvable  # end < start
    # expanded past empty inherits between's partiality (a 6s span shrunk by 4s/end)
    assert not Interval.between(Instant.at(2.0), Instant.at(8.0)).expanded(-4.0).is_resolvable
    assert not Interval.of(Instant.at(0.0), Duration.of(-1.0)).is_resolvable  # negative duration
    assert not Interval.around(Instant.at(0.0), Duration.of(-1.0)).is_resolvable  # negative radius
    disjoint = Interval.between(Instant.at(0.0), Instant.at(1.0)).intersection(
        Interval.between(Instant.at(5.0), Instant.at(6.0))
    )
    decision = disjoint.decide()
    assert isinstance(decision, Unresolvable)
    assert "disjoint" in decision.reason


def test_value_invariant() -> None:
    with pytest.raises(ValueError, match="precedes start"):
        IntervalValue(start=3.0, end=1.0)
    assert repr(IntervalValue(1.0, 2.5)) == "IntervalValue([1, 2.5])"


def test_contains_and_overlaps() -> None:
    span = Interval.between(Instant.at(0.0), Instant.at(10.0))
    assert span.contains(5.0).resolve() is True
    assert span.contains(Instant.at(10.0)).resolve() is True  # closed at the end
    assert span.contains(11.0).resolve() is False
    assert span.overlaps(Interval.between(Instant.at(5.0), Instant.at(15.0))).resolve() is True
    assert span.overlaps(Interval.between(Instant.at(10.0), Instant.at(20.0))).resolve() is True  # touching counts
    assert span.overlaps(Interval.between(Instant.at(11.0), Instant.at(20.0))).resolve() is False
