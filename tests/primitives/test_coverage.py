"""Coverage — disjoint spans, normalization, and the total set algebra."""

from __future__ import annotations

from fungeom import Coverage, Instant, Interval, Unresolvable
from fungeom.values import CoverageValue, IntervalValue


def span(start: float, end: float) -> Interval:
    return Interval.between(Instant.at(start), Instant.at(end))


def test_of_normalizes_and_merges() -> None:
    # unsorted, overlapping input collapses to a canonical disjoint set
    cov = Coverage.of([span(2.0, 5.0), span(0.0, 3.0), span(8.0, 9.0)]).resolve()
    assert cov.intervals == (IntervalValue(0.0, 5.0), IntervalValue(8.0, 9.0))
    assert cov.total_duration == 6.0
    assert Coverage.empty.resolve().is_empty


def test_union_and_total_duration() -> None:
    a = Coverage.of([span(0.0, 2.0)])
    b = Coverage.of([span(5.0, 7.0)])
    assert a.union(b).resolve() == CoverageValue((IntervalValue(0.0, 2.0), IntervalValue(5.0, 7.0)))
    assert a.union(b).total_duration().resolve() == 4.0


def test_intersection() -> None:
    a = Coverage.of([span(0.0, 6.0), span(8.0, 12.0)])
    b = Coverage.of([span(4.0, 10.0)])
    assert a.intersection(b).resolve() == CoverageValue((IntervalValue(4.0, 6.0), IntervalValue(8.0, 10.0)))
    # no overlap -> empty (total, not Unresolvable)
    disjoint = Coverage.of([span(0.0, 1.0)]).intersection(Coverage.of([span(5.0, 6.0)]))
    assert disjoint.resolve().is_empty


def test_difference() -> None:
    a = Coverage.of([span(0.0, 10.0)])
    b = Coverage.of([span(2.0, 4.0), span(6.0, 8.0)])
    # carving two holes out of one span leaves three closed pieces (endpoints survive)
    assert a.difference(b).resolve() == CoverageValue(
        (IntervalValue(0.0, 2.0), IntervalValue(4.0, 6.0), IntervalValue(8.0, 10.0))
    )
    # a hole flush with the left edge leaves no degenerate piece there
    assert Coverage.of([span(0.0, 5.0)]).difference(Coverage.of([span(0.0, 2.0)])).resolve() == CoverageValue(
        (IntervalValue(2.0, 5.0),)
    )
    # subtracting a superset is empty; a disjoint subtrahend changes nothing
    assert Coverage.of([span(0.0, 4.0)]).difference(Coverage.of([span(-1.0, 9.0)])).resolve().is_empty
    assert Coverage.of([span(0.0, 4.0)]).difference(Coverage.of([span(7.0, 9.0)])).resolve() == CoverageValue(
        (IntervalValue(0.0, 4.0),)
    )
    # a subtrahend entirely to the left of the span is skipped
    assert Coverage.of([span(5.0, 10.0)]).difference(Coverage.of([span(0.0, 2.0)])).resolve() == CoverageValue(
        (IntervalValue(5.0, 10.0),)
    )


def test_hull_and_gaps() -> None:
    cov = Coverage.of([span(0.0, 2.0), span(5.0, 7.0), span(9.0, 10.0)])
    assert cov.hull().resolve() == IntervalValue(0.0, 10.0)
    assert cov.gaps().resolve() == CoverageValue((IntervalValue(2.0, 5.0), IntervalValue(7.0, 9.0)))
    # fewer than two spans -> no gaps
    assert Coverage.of([span(0.0, 1.0)]).gaps().resolve().is_empty


def test_hull_of_empty_is_unresolvable() -> None:
    decision = Coverage.empty.hull().decide()
    assert isinstance(decision, Unresolvable)
    assert "empty" in decision.reason


def test_repr() -> None:
    cov = Coverage.of([span(0.0, 2.0), span(5.0, 7.0)]).resolve()
    assert repr(cov) == "CoverageValue([[0, 2], [5, 7]])"


def test_contains() -> None:
    cov = Coverage.of([span(0.0, 2.0), span(5.0, 7.0)])
    assert cov.contains(1.0).resolve() is True
    assert cov.contains(6.0).resolve() is True
    assert cov.contains(3.0).resolve() is False  # in the gap
    assert Coverage.empty.contains(0.0).resolve() is False
