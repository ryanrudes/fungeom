"""The ``Scalar`` interface and its arithmetic.

Operators accept a bare ``float`` or another ``Scalar`` and coerce the
former into a literal — so numbers stay ergonomic at the surface while always
becoming graph nodes underneath. Sibling resolver types are imported lazily to
keep module load acyclic.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool


class Scalar(Resolver[float]):
    """A deferred real number.

    Construct one with :meth:`of`; compose with the usual operators
    (``+ - * / **``, ``abs``) and :meth:`min`, :meth:`max`, :meth:`sqrt`,
    :meth:`clamp`, :meth:`sign`, :meth:`floor`, :meth:`ceil`, :meth:`round`,
    :meth:`mod` — each returns a new ``Scalar`` — plus the ordered comparisons
    :meth:`lt`, :meth:`le`, :meth:`gt`, :meth:`ge` (→ :class:`~fungeom.Bool`).
    ``resolve()`` yields a ``float`` (``Scalar.Value``). Bare numbers passed to
    these methods are lifted into literal scalars automatically, so
    ``v.scale(2.0)`` and ``v.scale(other.norm())`` both work.

    Some operations are *partial*: dividing by a scalar that resolves to zero, or
    ``sqrt`` of a negative, is :class:`~fungeom.Unresolvable` rather than
    an error — see :meth:`decide`.

    Comparisons return a deferred ``Bool``, *not* a Python ``bool`` — they are
    value-dependent and can themselves be ``Unresolvable`` — so the comparison
    operators (``<``, ``<=``, …) are deliberately **not** overloaded (that would
    force eager truth and silently break ``sorted``/``min``/``max``). Use the
    named methods.
    """

    type Value = float
    """The resolved value type — a plain ``float``."""

    @classmethod
    def of(cls, value: float | Scalar) -> Scalar:
        """A literal scalar (an existing ``Scalar`` is returned unchanged)."""
        if isinstance(value, Scalar):
            return value
        from fungeom.primitives.scalar.resolvers.literal import LiteralScalar
        from fungeom.primitives.scalar.value import as_scalar

        return LiteralScalar(value=as_scalar(value))

    def __add__(self, other: float | Scalar) -> Scalar:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.sum import SumScalar

        return SumScalar(a=self, b=as_scalar_resolver(other))

    def __radd__(self, other: float | Scalar) -> Scalar:
        return self.__add__(other)

    def __neg__(self) -> Scalar:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.product import ProductScalar

        return ProductScalar(a=self, b=as_scalar_resolver(-1.0))

    def __sub__(self, other: float | Scalar) -> Scalar:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return self.__add__(-as_scalar_resolver(other))

    def __mul__(self, other: float | Scalar) -> Scalar:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.product import ProductScalar

        return ProductScalar(a=self, b=as_scalar_resolver(other))

    def __rmul__(self, other: float | Scalar) -> Scalar:
        return self.__mul__(other)

    def __truediv__(self, other: float | Scalar) -> Scalar:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.quotient import QuotientScalar

        return QuotientScalar(numerator=self, denominator=as_scalar_resolver(other))

    def __pow__(self, other: float | Scalar) -> Scalar:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.power import PowerScalar

        return PowerScalar(base=self, exponent=as_scalar_resolver(other))

    def __abs__(self) -> Scalar:
        from fungeom.primitives.scalar.resolvers.absolute import AbsScalar

        return AbsScalar(value=self)

    def sqrt(self) -> Scalar:
        """The square root (Unresolvable if this resolves negative)."""
        from fungeom.primitives.scalar.resolvers.sqrt import SqrtScalar

        return SqrtScalar(value=self)

    def min(self, other: float | Scalar) -> Scalar:
        """The smaller of this scalar and ``other``."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.minimum import MinScalar

        return MinScalar(a=self, b=as_scalar_resolver(other))

    def max(self, other: float | Scalar) -> Scalar:
        """The larger of this scalar and ``other``."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.maximum import MaxScalar

        return MaxScalar(a=self, b=as_scalar_resolver(other))

    def clamp(self, low: float | Scalar, high: float | Scalar) -> Scalar:
        """This scalar clamped to ``[low, high]`` (Unresolvable if ``low > high``)."""
        from fungeom.primitives.scalar.resolvers.clamp import ClampScalar
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return ClampScalar(value=self, low=as_scalar_resolver(low), high=as_scalar_resolver(high))

    def sign(self) -> Scalar:
        """The sign of this scalar: ``-1``, ``0``, or ``1`` (as a float)."""
        from fungeom.primitives.scalar.resolvers.sign import SignScalar

        return SignScalar(value=self)

    def floor(self) -> Scalar:
        """The greatest integer ≤ this scalar (as a float)."""
        from fungeom.primitives.scalar.resolvers.floor import FloorScalar

        return FloorScalar(value=self)

    def ceil(self) -> Scalar:
        """The least integer ≥ this scalar (as a float)."""
        from fungeom.primitives.scalar.resolvers.ceil import CeilScalar

        return CeilScalar(value=self)

    def round(self) -> Scalar:
        """This scalar rounded to the nearest integer (ties to even; as a float)."""
        from fungeom.primitives.scalar.resolvers.round import RoundScalar

        return RoundScalar(value=self)

    def mod(self, modulus: float | Scalar) -> Scalar:
        """This scalar modulo ``modulus`` (Unresolvable if ``modulus`` resolves to zero)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.scalar.resolvers.modulo import ModScalar

        return ModScalar(value=self, modulus=as_scalar_resolver(modulus))

    def lt(self, other: float | Scalar) -> Bool:
        """Whether this scalar is strictly less than ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessThan
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return LessThan(a=self, b=as_scalar_resolver(other))

    def le(self, other: float | Scalar) -> Bool:
        """Whether this scalar is less than or equal to ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessEqual
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return LessEqual(a=self, b=as_scalar_resolver(other))

    def gt(self, other: float | Scalar) -> Bool:
        """Whether this scalar is strictly greater than ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessThan
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return LessThan(a=as_scalar_resolver(other), b=self)

    def ge(self, other: float | Scalar) -> Bool:
        """Whether this scalar is greater than or equal to ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessEqual
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return LessEqual(a=as_scalar_resolver(other), b=self)
