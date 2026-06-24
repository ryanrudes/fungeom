"""The ``Bool`` interface — deferred truth values and their logical algebra.

A boolean question can itself be *unanswerable*: comparing two scalars one of
which is :class:`~fungeom.Unresolvable` has no truth value. So a ``Bool`` is a
first-class deferred resolver like every other primitive — produced by the
comparison / predicate methods on the ordered and spanning types
(:meth:`~fungeom.Scalar.lt`, :meth:`~fungeom.Instant.before`,
:meth:`~fungeom.Interval.contains`, …) and composed with the logical algebra here.

It sits just above ``core`` (below ``scalar``): the comparison resolvers live
under their *source* primitive and resolve *into* a ``Bool``, exactly as
``Vec3.norm`` lives under ``vec3`` and resolves into a ``Scalar``.

**Propagation is strict.** ``a & b`` is ``Unresolvable`` if *either* side is —
uniform with every other combinator in the library. A Kleene three-valued
short-circuit (where ``False & undefined`` would be ``False``) is a deliberate
non-goal for now: it would break the propagation invariant the whole design rests
on, and here ``Unresolvable`` means *undefined*, not epistemic *unknown*.
"""

from __future__ import annotations

from typing import ClassVar

from fungeom.core.resolver import Resolver


class Bool(Resolver[bool]):
    """A deferred truth value — the decidable answer to a yes/no question.

    Construct one with :meth:`of` or the :attr:`true` / :attr:`false` constants;
    compose with :meth:`and_` (``&``), :meth:`or_` (``|``), and :meth:`not_`
    (``~``). ``resolve()`` yields a ``bool`` (``Bool.Value``). Every logical op is
    *total* — partiality arises only by propagation from an unresolvable operand
    (typically an unresolvable comparison).
    """

    type Value = bool
    """The resolved value type — a plain ``bool``."""

    true: ClassVar[Bool]
    """The constant ``True``, as a resolver. (Assigned once ``LiteralBool`` exists.)"""

    false: ClassVar[Bool]
    """The constant ``False``, as a resolver. (Assigned once ``LiteralBool`` exists.)"""

    @classmethod
    def of(cls, value: bool | Bool) -> Bool:
        """A literal truth value (an existing ``Bool`` is returned unchanged)."""
        if isinstance(value, Bool):
            return value
        from fungeom.primitives.boolean.resolvers.literal import LiteralBool
        from fungeom.primitives.boolean.value import as_bool

        return LiteralBool(value=as_bool(value))

    def and_(self, other: bool | Bool) -> Bool:
        """Logical conjunction — ``True`` iff both this and ``other`` are."""
        from fungeom.primitives.boolean.resolvers.conjunction import AndBool

        return AndBool(a=self, b=Bool.of(other))

    def or_(self, other: bool | Bool) -> Bool:
        """Logical disjunction — ``True`` iff this or ``other`` is."""
        from fungeom.primitives.boolean.resolvers.disjunction import OrBool

        return OrBool(a=self, b=Bool.of(other))

    def not_(self) -> Bool:
        """Logical negation."""
        from fungeom.primitives.boolean.resolvers.negation import NotBool

        return NotBool(value=self)

    def __and__(self, other: bool | Bool) -> Bool:
        return self.and_(other)

    def __rand__(self, other: bool | Bool) -> Bool:
        return self.and_(other)

    def __or__(self, other: bool | Bool) -> Bool:
        return self.or_(other)

    def __ror__(self, other: bool | Bool) -> Bool:
        return self.or_(other)

    def __invert__(self) -> Bool:
        return self.not_()
