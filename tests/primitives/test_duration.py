"""Duration — construction, affine arithmetic, and the zero-denominator ratio."""

from __future__ import annotations

from fungeom import Duration, Scalar, Unresolvable


def test_of_units_and_idempotence() -> None:
    assert Duration.of(2.0).resolve() == 2.0
    assert Duration.seconds(3.0).resolve() == 3.0
    assert Duration.milliseconds(1500.0).resolve() == 1.5
    assert Duration.minutes(2.0).resolve() == 120.0
    assert Duration.zero.resolve() == 0.0
    d = Duration.of(4.0)
    assert Duration.of(d) is d  # an existing Duration is returned unchanged
    assert Duration.of(Scalar.of(5.0)).resolve() == 5.0  # deferred scalar seconds


def test_arithmetic() -> None:
    two, three = Duration.of(2.0), Duration.of(3.0)
    assert (two + three).resolve() == 5.0
    assert (three - two).resolve() == 1.0
    assert (-two).resolve() == -2.0
    assert (two * 3.0).resolve() == 6.0
    assert (3.0 * two).resolve() == 6.0  # reflected
    assert two.scale(Scalar.of(2.5)).resolve() == 5.0
    assert (Duration.of(6.0) / 2.0).resolve() == 3.0
    assert abs(Duration.of(-4.0)).resolve() == 4.0


def test_ratio_value() -> None:
    assert Duration.of(6.0).ratio(Duration.of(2.0)).resolve() == 3.0


def test_order_reductions() -> None:
    two, five = Duration.of(2.0), Duration.of(5.0)
    assert two.min(five).resolve() == 2.0
    assert two.max(five).resolve() == 5.0
    assert Duration.of(-3.0).min(two).resolve() == -3.0
    assert Duration.of(-3.0).max(two).resolve() == 2.0
    assert Duration.of(7.0).clamp(two, five).resolve() == 5.0
    assert Duration.of(1.0).clamp(two, five).resolve() == 2.0
    assert Duration.of(3.0).clamp(two, five).resolve() == 3.0


def test_comparisons() -> None:
    short, long_ = Duration.of(2.0), Duration.of(5.0)
    assert short.lt(long_).resolve() is True
    assert long_.lt(short).resolve() is False
    assert short.le(short).resolve() is True
    assert long_.gt(short).resolve() is True
    assert short.ge(long_).resolve() is False
    assert long_.ge(long_).resolve() is True
    assert short.lt(5.0).resolve() is True  # bare seconds coerce
    # signed order: a more-negative duration is "shorter"
    assert Duration.of(-3.0).lt(short).resolve() is True


def test_partialities() -> None:
    assert isinstance(Duration.of(1.0).ratio(Duration.zero).decide(), Unresolvable)
    assert isinstance(Duration.of(1.0).ratio(Duration.of(0.0)).decide(), Unresolvable)
    # clamp with inverted bounds has no sensible answer
    assert isinstance(Duration.of(3.0).clamp(Duration.of(5.0), Duration.of(2.0)).decide(), Unresolvable)
