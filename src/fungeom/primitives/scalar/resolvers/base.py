"""The ``Scalar`` interface and its arithmetic.

Operators accept a bare ``float`` or another ``Scalar`` and coerce the
former into a literal — so numbers stay ergonomic at the surface while always
becoming graph nodes underneath. Sibling resolver types are imported lazily to
keep module load acyclic.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver


class Scalar(Resolver[float]):
    """A deferred real number.

    Construct one with :meth:`of`; compose with the usual operators
    (``+ - * / **``, ``abs``) and :meth:`min`, :meth:`max`, :meth:`sqrt`,
    :meth:`clamp` — each returns a new ``Scalar``. ``resolve()`` yields a
    ``float`` (``Scalar.Value``). Bare numbers passed to these methods are lifted
    into literal scalars automatically, so ``v.scale(2.0)`` and
    ``v.scale(other.norm())`` both work.

    Some operations are *partial*: dividing by a scalar that resolves to zero, or
    ``sqrt`` of a negative, is :class:`~fungeom.Unresolvable` rather than
    an error — see :meth:`decide`.
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
