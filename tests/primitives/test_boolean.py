"""Bool — deferred truth values, logical algebra, and strict (non-Kleene) propagation."""

from __future__ import annotations

from fungeom import Bool, Scalar, Unresolvable


def test_constructors() -> None:
    assert Bool.of(True).resolve() is True
    assert Bool.of(False).resolve() is False
    assert Bool.true.resolve() is True
    assert Bool.false.resolve() is False
    b = Bool.of(True)
    assert Bool.of(b) is b  # an existing Bool is returned unchanged


def test_logical_algebra() -> None:
    t, f = Bool.true, Bool.false
    assert t.and_(t).resolve() is True
    assert t.and_(f).resolve() is False
    assert f.or_(t).resolve() is True
    assert f.or_(f).resolve() is False
    assert t.not_().resolve() is False
    # operators
    assert (t & f).resolve() is False
    assert (t | f).resolve() is True
    assert (~t).resolve() is False
    # bare bools coerce, on either side
    assert (t & True).resolve() is True
    assert (True & t).resolve() is True  # __rand__
    assert (False | t).resolve() is True  # __ror__


def test_strict_propagation_not_kleene() -> None:
    bad = Scalar.of(1).lt(Scalar.of(1) / Scalar.of(0))  # an unresolvable comparison
    assert isinstance(bad.decide(), Unresolvable)
    # strict: any unresolvable operand poisons the result — *no* Kleene short-circuit,
    # so even `False and ⊥` / `True or ⊥` stay Unresolvable.
    assert isinstance(Bool.false.and_(bad).decide(), Unresolvable)
    assert isinstance(Bool.true.or_(bad).decide(), Unresolvable)
    assert isinstance(bad.not_().decide(), Unresolvable)
