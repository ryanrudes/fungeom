"""The ``Duration`` interface and its arithmetic.

A duration is the **difference** vector space of the temporal pair (the
``Instant`` is the affine point space). It mirrors ``Scalar``/``Vec3``: durations
add and subtract to durations, negate, scale by a (deferred) scalar, divide by a
scalar, and take a dimensionless :meth:`ratio` against another duration. Sibling
resolver types are imported lazily to keep module load acyclic; the lower-layer
:class:`~fungeom.Scalar` is imported normally.
"""

from __future__ import annotations

from typing import ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.scalar.resolvers.base import Scalar


class Duration(Resolver[float]):
    """A deferred elapsed time — a *signed* span of seconds.

    Construct one with the unit-bearing :meth:`of`, :meth:`seconds`,
    :meth:`milliseconds`, :meth:`minutes`, or the :attr:`zero` constant; compose
    with the usual operators (``+ - *``, ``/`` by a scalar, ``abs``, unary
    ``-``), the :meth:`scale` alias, :meth:`ratio` (→ a dimensionless
    :class:`~fungeom.Scalar`), the order reductions :meth:`min` / :meth:`max`
    / :meth:`clamp`, and the order comparisons :meth:`lt` / :meth:`le` / :meth:`gt`
    / :meth:`ge` (→ :class:`~fungeom.Bool`). ``resolve()`` yields a ``float`` of
    seconds (``Duration.Value``).

    Durations form a vector space, so there is no absolute origin here — that is
    what an :class:`~fungeom.Instant` provides. The one *partial* operation is
    :meth:`ratio`: dividing by a duration that resolves to zero is
    :class:`~fungeom.Unresolvable` rather than an error — see :meth:`decide`.
    """

    type Value = float
    """The resolved value type — a plain ``float`` of seconds."""

    zero: ClassVar[Duration]
    """The zero duration, as a resolver. (Assigned once ``LiteralDuration`` exists.)"""

    @classmethod
    def of(cls, seconds: float | Scalar | Duration) -> Duration:
        """A duration of ``seconds`` (an existing ``Duration`` is returned unchanged).

        A deferred :class:`~fungeom.Scalar` number of seconds becomes the
        one-second duration scaled by that scalar, keeping it a graph node.
        """
        from fungeom.primitives.duration.resolvers.literal import (
            LiteralDuration,
            as_duration_resolver,
        )

        if isinstance(seconds, Scalar):
            return LiteralDuration(value=1.0).scale(seconds)
        return as_duration_resolver(seconds)

    @classmethod
    def seconds(cls, value: float | Scalar) -> Duration:
        """A duration of ``value`` seconds."""
        return cls.of(value)

    @classmethod
    def milliseconds(cls, value: float | Scalar) -> Duration:
        """A duration of ``value`` milliseconds (``value / 1000`` seconds)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return cls.of(as_scalar_resolver(value) / 1000.0)

    @classmethod
    def minutes(cls, value: float | Scalar) -> Duration:
        """A duration of ``value`` minutes (``value * 60`` seconds)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return cls.of(as_scalar_resolver(value) * 60.0)

    def __add__(self, other: Duration) -> Duration:
        from fungeom.primitives.duration.resolvers.sum import SumDuration

        return SumDuration(a=self, b=other)

    def __sub__(self, other: Duration) -> Duration:
        from fungeom.primitives.duration.resolvers.sum import SumDuration

        return SumDuration(a=self, b=-other)

    def __neg__(self) -> Duration:
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return self.scale(as_scalar_resolver(-1.0))

    def scale(self, factor: float | Scalar) -> Duration:
        """This duration scaled by a (deferred) factor."""
        from fungeom.primitives.duration.resolvers.scaled import ScaledDuration
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return ScaledDuration(duration=self, factor=as_scalar_resolver(factor))

    def __mul__(self, other: float | Scalar) -> Duration:
        return self.scale(other)

    def __rmul__(self, other: float | Scalar) -> Duration:
        return self.scale(other)

    def __truediv__(self, other: float | Scalar) -> Duration:
        """This duration divided by a *scalar* (not a duration — use :meth:`ratio` for that)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return self.scale(as_scalar_resolver(1.0) / as_scalar_resolver(other))

    def ratio(self, other: Duration) -> Scalar:
        """The dimensionless ratio ``self / other`` (Unresolvable if ``other`` is zero)."""
        from fungeom.primitives.duration.resolvers.ratio import DurationRatio

        return DurationRatio(numerator=self, denominator=other)

    def __abs__(self) -> Duration:
        from fungeom.primitives.duration.resolvers.absolute import AbsDuration

        return AbsDuration(value=self)

    def min(self, other: Duration) -> Duration:
        """The shorter of this duration and ``other`` (durations are totally ordered)."""
        from fungeom.primitives.duration.resolvers.minimum import MinDuration

        return MinDuration(a=self, b=other)

    def max(self, other: Duration) -> Duration:
        """The longer of this duration and ``other`` (durations are totally ordered)."""
        from fungeom.primitives.duration.resolvers.maximum import MaxDuration

        return MaxDuration(a=self, b=other)

    def clamp(self, low: Duration, high: Duration) -> Duration:
        """This duration clamped into ``[low, high]`` (Unresolvable if ``low > high``)."""
        from fungeom.primitives.duration.resolvers.clamp import ClampDuration

        return ClampDuration(value=self, low=low, high=high)

    def lt(self, other: Duration | float) -> Bool:
        """Whether this duration is strictly shorter than ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessThan

        return LessThan(a=self, b=Duration.of(other))

    def le(self, other: Duration | float) -> Bool:
        """Whether this duration is shorter than or equal to ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessEqual

        return LessEqual(a=self, b=Duration.of(other))

    def gt(self, other: Duration | float) -> Bool:
        """Whether this duration is strictly longer than ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessThan

        return LessThan(a=Duration.of(other), b=self)

    def ge(self, other: Duration | float) -> Bool:
        """Whether this duration is longer than or equal to ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessEqual

        return LessEqual(a=Duration.of(other), b=self)
