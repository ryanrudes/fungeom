"""Scalar — construction, arithmetic, and value-dependent partialities."""

from __future__ import annotations

from fungeom import Scalar, Unresolvable


def test_of_and_idempotence() -> None:
    assert Scalar.of(2.0).resolve() == 2.0
    s = Scalar.of(3.0)
    assert Scalar.of(s) is s  # an existing Scalar is returned unchanged


def test_arithmetic_and_reflected_operands() -> None:
    two, three = Scalar.of(2.0), Scalar.of(3.0)
    assert (two + three).resolve() == 5.0
    assert (three - two).resolve() == 1.0
    assert (two * three).resolve() == 6.0
    assert (three / two).resolve() == 1.5
    assert (-two).resolve() == -2.0
    assert (two ** Scalar.of(10)).resolve() == 1024.0
    # bare numbers coerce, including in reflected position
    assert (2.0 + three).resolve() == 5.0
    assert (2.0 * three).resolve() == 6.0
    assert (three - 1).resolve() == 2.0
    assert (three / 1).resolve() == 3.0


def test_min_max_abs_sqrt_clamp() -> None:
    assert Scalar.of(3.0).min(5.0).resolve() == 3.0
    assert Scalar.of(3.0).max(5.0).resolve() == 5.0
    assert abs(Scalar.of(-4.0)).resolve() == 4.0
    assert Scalar.of(9.0).sqrt().resolve() == 3.0
    assert Scalar.of(5.0).clamp(0.0, 3.0).resolve() == 3.0
    assert Scalar.of(-1.0).clamp(0.0, 3.0).resolve() == 0.0
    assert Scalar.of(2.0).clamp(0.0, 3.0).resolve() == 2.0


def test_sign_floor_ceil_round() -> None:
    assert Scalar.of(-3.5).sign().resolve() == -1.0
    assert Scalar.of(0.0).sign().resolve() == 0.0
    assert Scalar.of(2.5).sign().resolve() == 1.0
    assert Scalar.of(2.7).floor().resolve() == 2.0
    assert Scalar.of(-2.1).floor().resolve() == -3.0
    assert Scalar.of(2.1).ceil().resolve() == 3.0
    assert Scalar.of(-2.9).ceil().resolve() == -2.0
    assert Scalar.of(2.5).round().resolve() == 2.0  # ties to even
    assert Scalar.of(3.5).round().resolve() == 4.0


def test_mod() -> None:
    assert Scalar.of(7.0).mod(3.0).resolve() == 1.0
    assert Scalar.of(-1.0).mod(3.0).resolve() == 2.0  # result follows the modulus' sign


def test_partialities() -> None:
    assert isinstance((Scalar.of(1.0) / Scalar.of(0.0)).decide(), Unresolvable)  # /0
    assert isinstance(Scalar.of(-1.0).sqrt().decide(), Unresolvable)  # sqrt(<0)
    assert isinstance((Scalar.of(-1.0) ** Scalar.of(0.5)).decide(), Unresolvable)  # complex
    assert isinstance((Scalar.of(0.0) ** Scalar.of(-1.0)).decide(), Unresolvable)  # 0 ** -1
    assert isinstance(Scalar.of(2.0).clamp(3.0, 0.0).decide(), Unresolvable)  # low > high
    assert isinstance(Scalar.of(1.0).mod(0.0).decide(), Unresolvable)  # mod 0


def test_comparisons() -> None:
    one, two = Scalar.of(1.0), Scalar.of(2.0)
    assert one.lt(two).resolve() is True
    assert two.lt(one).resolve() is False
    assert one.le(one).resolve() is True
    assert two.gt(one).resolve() is True
    assert one.ge(two).resolve() is False
    assert two.ge(two).resolve() is True
    assert one.lt(5.0).resolve() is True  # bare numbers coerce
