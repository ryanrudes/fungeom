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
