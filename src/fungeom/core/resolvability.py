"""Resolvability: evidence about whether a resolver can be resolved.

Deciding whether a :class:`~fungeom.core.resolver.Resolver` can produce a
value is itself a computation over its graph. Rather than collapse that into a
bare ``bool`` (which would throw away *why* something cannot be resolved), the
decision is reified as a small sum type:

* :class:`Resolvable` — proof that resolution succeeds, carrying the value it
  computed along the way (so a later ``resolve()`` is free).
* :class:`Unresolvable` — proof that it does not, carrying a human-readable
  reason.

``Resolvability[T] = Resolvable[T] | Unresolvable`` is what ``Resolver.decide()``
returns. :class:`Unresolvable` is deliberately *not* generic: a failure carries
only a reason, so the same value can flow out of a ``Vec3`` decision and into a
``Point3`` one without rewrapping. Because the decision is an ordinary value, you
can pass it around, ``match`` on it, or require :class:`Resolvable` in a function
signature to demand a *proven-resolvable* input at type-check time.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, NoReturn


class UnresolvableError(Exception):
    """Raised when something that cannot be resolved is asked to resolve."""


@dataclass(frozen=True)
class Resolvable[T]:
    """Evidence that a resolver resolves, carrying the computed value."""

    value: T

    ok: ClassVar[bool] = True

    def unwrap(self) -> T:
        """Return the resolved value."""
        return self.value


@dataclass(frozen=True)
class Unresolvable:
    """Evidence that a resolver does not resolve, and why."""

    reason: str

    ok: ClassVar[bool] = False

    def unwrap(self) -> NoReturn:
        """Raise :class:`UnresolvableError` with the captured reason."""
        raise UnresolvableError(self.reason)


type Resolvability[T] = Resolvable[T] | Unresolvable
"""The result of :meth:`~fungeom.core.resolver.Resolver.decide`."""


def gather[T](decisions: Iterable[Resolvability[T]]) -> Resolvability[list[T]]:
    """Collect many decisions into one.

    Returns :class:`Resolvable` with every value once they all succeed, or the
    first :class:`Unresolvable` encountered. This is the ``traverse`` that makes
    N-ary combinators (a centroid, a polyline, ...) short and uniform.
    """
    values: list[T] = []
    for decision in decisions:
        if isinstance(decision, Unresolvable):
            return decision
        values.append(decision.value)
    return Resolvable(values)
