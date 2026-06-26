"""BoolSignal — a three-valued temporal predicate with exact sub-sample crossings."""

from __future__ import annotations

from fungeom import BoolSignal, ScalarSignal, Unresolvable
from fungeom.values import BoolSeries, CoverageValue, IntervalValue


def _height() -> ScalarSignal:
    # dips below 0 between exact crossings t=1.5 and t=2.5
    return ScalarSignal.from_samples([0, 1, 2, 3, 4], [2, 1, -1, 1, 2])


def test_threshold_crossings_are_exact() -> None:
    contact = _height().lt(0.0)
    assert isinstance(contact, BoolSignal)
    assert isinstance(contact.resolve(), BoolSeries)
    assert contact.when_true().resolve() == CoverageValue((IntervalValue(1.5, 2.5),))  # sub-sample exact
    assert contact.at(2.0).resolve() is True
    assert contact.at(0.5).resolve() is False
    assert contact.first_true().resolve() == 1.5


def test_ge_and_when_false() -> None:
    above = _height().ge(0.0)
    assert above.when_true().resolve() == CoverageValue((IntervalValue(0, 1.5), IntervalValue(2.5, 4)))
    # when_false is the defined-and-false complement
    assert _height().lt(0.0).when_false().resolve() == CoverageValue((IntervalValue(0, 1.5), IntervalValue(2.5, 4)))


def test_le_ge_flat_segment_distinguishes_strictness() -> None:
    # a segment sitting exactly on the threshold: lt excludes it, le includes it
    flat = ScalarSignal.from_samples([0, 1, 2], [0, 0, 1])
    assert flat.lt(0.0).when_true().resolve().is_empty  # strictly below 0: never (the flat part is == 0)
    assert flat.le(0.0).when_true().resolve() == CoverageValue((IntervalValue(0, 1),))  # ≤ 0 includes the flat part


def test_bool_series_repr() -> None:
    assert "BoolSeries" in repr(_height().lt(0.0).resolve())


def test_never_true_first_true_is_unresolvable() -> None:
    assert isinstance(_height().lt(-10.0).first_true().decide(), Unresolvable)
    assert _height().lt(-10.0).when_true().resolve().is_empty


def test_logical_algebra_is_strict() -> None:
    contact = _height().lt(0.0)  # true over [1.5, 2.5]
    warm = ScalarSignal.from_samples([0, 4], [1, 1]).gt(0.0)  # true over all [0, 4]
    assert (contact & warm).when_true().resolve() == CoverageValue((IntervalValue(1.5, 2.5),))
    assert (contact | _height().gt(1.5)).when_true().resolve() == CoverageValue(
        (IntervalValue(0, 0.5), IntervalValue(1.5, 2.5), IntervalValue(3.5, 4))
    )
    # ~ is the complement within support
    assert (~contact).when_true().resolve() == CoverageValue((IntervalValue(0, 1.5), IntervalValue(2.5, 4)))


def test_three_valued_gap_is_unresolvable_not_false() -> None:
    gapped = ScalarSignal.from_samples([0, 1, 5, 6], [1, -1, -1, 1], max_gap=2.0).lt(0.0)
    # true-spans live within each defined run (never bridging the gap)
    assert gapped.when_true().resolve() == CoverageValue((IntervalValue(0.5, 1), IntervalValue(5, 5.5)))
    assert isinstance(gapped.at(3.0).decide(), Unresolvable)  # inside the gap → undefined, not False
    assert gapped.at(0.75).resolve() is True
    assert gapped.support().resolve() == CoverageValue((IntervalValue(0, 1), IntervalValue(5, 6)))


def test_isolated_sample_and_strict_combinator_supports() -> None:
    # an isolated sample (its own degenerate span) contributes a point when it satisfies
    isolated = ScalarSignal.from_samples([0, 5, 6], [-1, -1, 1], max_gap=2.0).lt(0.0)
    assert isolated.when_true().resolve() == CoverageValue((IntervalValue(0, 0), IntervalValue(5, 5.5)))
    # strict AND: the support narrows to the overlap of the two operands' supports
    a = ScalarSignal.from_samples([0, 4], [-1, -1]).lt(0.0)  # support [0,4]
    b = ScalarSignal.from_samples([2, 6], [-1, -1]).lt(0.0)  # support [2,6]
    assert (a & b).support().resolve() == CoverageValue((IntervalValue(2, 4),))


def test_propagation_from_a_bad_signal() -> None:
    bad = ScalarSignal.from_samples([1, 0], [1, 2])  # out-of-order → Unresolvable
    assert isinstance(bad.lt(0.0).decide(), Unresolvable)
    assert isinstance(bad.lt(0.0).at(0.5).decide(), Unresolvable)
    assert isinstance(bad.lt(0.0).when_true().decide(), Unresolvable)
    assert isinstance(bad.lt(0.0).first_true().decide(), Unresolvable)
    good = _height().lt(0.0)
    assert isinstance((bad.lt(0.0) & good).decide(), Unresolvable)
    assert isinstance((good & bad.lt(0.0)).decide(), Unresolvable)
    assert isinstance((bad.lt(0.0)).not_().decide(), Unresolvable)


def test_at_is_exact_at_threshold_touch_for_strict_predicates() -> None:
    # at an exact crossing the strict predicate is False (value is *on* the threshold), and a
    # predicate and its negation are never both True there (the three-valued contract)
    contact = _height().lt(0.0)  # crosses 0 exactly at t=1.5
    assert contact.at(1.5).resolve() is False  # value is exactly 0, and 0 < 0 is False
    assert (~contact).at(1.5).resolve() is True  # …so the negation is True — they disagree
    assert contact.at(1.5).resolve() != (~contact).at(1.5).resolve()
    # a left-endpoint sample sitting on the threshold is likewise False under a strict predicate
    assert ScalarSignal.from_samples([0, 1], [0, -1]).lt(0.0).at(0.0).resolve() is False


def test_non_strict_le_ge_include_an_interior_touchpoint() -> None:
    # a valley grazing the threshold at an interior vertex: le is True there (0 <= 0), and the
    # touch instant is reported by when_true as a degenerate point (consistent with at())
    valley = ScalarSignal.from_samples([0, 1, 2], [1, 0, 1]).le(0.0)
    assert valley.at(1.0).resolve() is True
    assert valley.when_true().resolve() == CoverageValue((IntervalValue(1.0, 1.0),))
    # the dual: a peak grazing from below under ge
    peak = ScalarSignal.from_samples([0, 1, 2], [-1, 0, -1]).ge(0.0)
    assert peak.at(1.0).resolve() is True


def test_composed_at_is_pointwise_and_strict() -> None:
    # & / | / ~ evaluate pointwise; a query where either operand is undefined (a gap) is Unresolvable
    a = ScalarSignal.from_samples([0, 1, 2, 3, 4], [2, 1, -1, 1, 2]).lt(0.0)  # true on (1.5, 2.5)
    b = ScalarSignal.from_samples([0, 1, 2, 3, 4], [-1, -1, -1, 1, 1]).lt(0.0)  # true on [0, ~2.5)
    assert (a & b).at(2.0).resolve() is True  # both true at t=2
    assert (a & b).at(0.5).resolve() is False  # a false at t=0.5
    assert (a | b).at(0.5).resolve() is True  # b true at t=0.5
    # a gap in one operand makes the conjunction undefined there (strict, not Kleene)
    gappy = ScalarSignal.from_samples([0, 1, 3, 4], [1, -1, -1, 1], max_gap=1.5).lt(0.0)  # gap over (1,3)
    assert isinstance((a & gappy).at(2.0).decide(), Unresolvable)


def test_last_true_is_the_release_instant() -> None:
    contact = _height().lt(0.0)  # true on [1.5, 2.5]
    assert contact.first_true().resolve() == 1.5  # touchdown
    assert contact.last_true().resolve() == 2.5  # release / lift-off
    # never true → Unresolvable, like first_true
    never = ScalarSignal.from_samples([0, 1], [1, 2]).lt(0.0)
    assert isinstance(never.last_true().decide(), Unresolvable)
