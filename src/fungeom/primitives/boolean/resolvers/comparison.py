"""Ordered comparisons of any two real-valued resolvers, resolving to a ``Bool``.

These are generic over ``Resolver[float]`` so a single pair of resolvers backs the
comparisons on *every* totally-ordered, float-valued primitive — ``Scalar.lt`` and
``Instant.before`` both build a :class:`LessThan`. The public facade methods stay
type-safe (``Scalar.lt`` takes a ``Scalar``, ``Instant.before`` an ``Instant``);
these concrete resolvers are private and never mix the two. ``gt`` / ``ge`` are
just these with the operands swapped, so only two concretes are needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool


@dataclass(frozen=True, eq=False)
class LessThan(Bool):
    """``a < b`` — resolvable iff both operands are."""

    a: Resolver[float]
    b: Resolver[float]

    def _decide(self) -> BoolDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a < b)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class LessEqual(Bool):
    """``a <= b`` — resolvable iff both operands are."""

    a: Resolver[float]
    b: Resolver[float]

    def _decide(self) -> BoolDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(a <= b)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
