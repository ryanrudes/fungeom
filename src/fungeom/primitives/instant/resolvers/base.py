"""The ``Instant`` interface and its combinators.

An instant is the **affine** point space of the temporal pair; durations are its
difference space (exactly as ``Point3`` relates to ``Vec3``). The affine algebra
is enforced here through the method types: ``Instant - Instant`` is a
:class:`~fungeom.primitives.duration.Duration`, ``Instant ± Duration`` is another
``Instant``, and there is deliberately **no** ``Instant + Instant`` (meaningless
in an affine space). Combinator methods construct sibling resolver types, so
those imports are deferred into the method bodies to keep module load acyclic;
the lower-layer :class:`~fungeom.Scalar` and ``Duration`` are imported normally.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import ClassVar, overload

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.scalar.resolvers.base import Scalar


class Instant(Resolver[float]):
    """A deferred point on the timeline — a number of seconds on the master clock.

    Construct one with :meth:`at`, the :attr:`epoch` constant, or the affine
    reductions :meth:`centroid` / :meth:`affine`; compose with ``+`` /
    :meth:`shifted_by` (by a :class:`~fungeom.primitives.duration.Duration` →
    another ``Instant``), ``-`` (which is overloaded: ``Instant - Instant`` →
    ``Duration``, ``Instant - Duration`` → ``Instant``), :meth:`duration_to`
    (→ ``Duration``), :meth:`lerp`, :meth:`midpoint`, the order reductions
    :meth:`min` / :meth:`max` (earliest / latest), and the order *predicates*
    :meth:`before` / :meth:`after` (→ :class:`~fungeom.Bool`). ``resolve()`` yields
    a ``float`` of seconds (``Instant.Value``).

    Instants form an affine space, so there is no ``Instant + Instant`` — only an
    instant plus a *displacement* (a duration), or a *weighted* combination whose
    weights total one (:meth:`affine`). The binary and shift operations are total;
    partiality arises in :meth:`centroid` / :meth:`affine` (empty / zero-total
    weight) and otherwise by propagation from an unresolvable input.
    """

    type Value = float
    """The resolved value type — a plain ``float`` of master-clock seconds."""

    epoch: ClassVar[Instant]
    """The master-clock origin (t = 0), as a resolver.

    This is the chosen chart origin, *not* an algebraic zero: instants are affine
    points and have no zero. It is simply the landmark every other instant is
    measured against. (Assigned once ``LiteralInstant`` exists.)
    """

    @classmethod
    def at(cls, t: float | Scalar) -> Instant:
        """The instant at ``t`` seconds on the master clock.

        A deferred :class:`~fungeom.Scalar` time is the :attr:`epoch` shifted by
        that many seconds, keeping it a graph node.
        """
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        if isinstance(t, Scalar):
            return cls.epoch.shifted_by(Duration.of(t))
        return as_instant_resolver(t)

    @classmethod
    def centroid(cls, instants: Iterable[Instant]) -> Instant:
        """The mean of ``instants`` (Unresolvable if there are none)."""
        from fungeom.primitives.instant.resolvers.centroid import CentroidInstant

        return CentroidInstant(instants=tuple(instants))

    @classmethod
    def affine(cls, instants: Sequence[Instant], weights: Sequence[float | Scalar]) -> Instant:
        """A weighted combination of ``instants`` (Unresolvable if weights total zero)."""
        from fungeom.primitives.instant.resolvers.affine import affine_combination

        return affine_combination(instants, weights)

    def shifted_by(self, by: Duration | float) -> Instant:
        """This instant advanced by a duration (a bare number is seconds)."""
        from fungeom.primitives.instant.resolvers.shifted import ShiftedInstant

        return ShiftedInstant(instant=self, by=Duration.of(by))

    def duration_to(self, other: Instant) -> Duration:
        """The duration from this instant to ``other`` (``other - self``)."""
        from fungeom.primitives.instant.resolvers.difference import InstantDuration

        return InstantDuration(later=other, earlier=self)

    def __add__(self, other: Duration | float) -> Instant:
        return self.shifted_by(other)

    @overload
    def __sub__(self, other: Instant) -> Duration: ...

    @overload
    def __sub__(self, other: Duration | float) -> Instant: ...

    def __sub__(self, other: Instant | Duration | float) -> Instant | Duration:
        """``Instant - Instant`` → ``Duration``; ``Instant - Duration`` → ``Instant``."""
        if isinstance(other, Instant):
            return other.duration_to(self)
        return self.shifted_by(-Duration.of(other))

    def lerp(self, other: Instant, t: float | Scalar) -> Instant:
        """Linearly interpolate toward ``other`` (``t=0`` here, ``t=1`` there)."""
        from fungeom.primitives.instant.resolvers.lerp import LerpInstant
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return LerpInstant(a=self, b=other, t=as_scalar_resolver(t))

    def midpoint(self, other: Instant) -> Instant:
        """The instant halfway between this instant and ``other``."""
        return self.lerp(other, 0.5)

    def min(self, other: Instant) -> Instant:
        """The earlier of this instant and ``other`` (instants are totally ordered)."""
        from fungeom.primitives.instant.resolvers.minimum import MinInstant

        return MinInstant(a=self, b=other)

    def max(self, other: Instant) -> Instant:
        """The later of this instant and ``other`` (instants are totally ordered)."""
        from fungeom.primitives.instant.resolvers.maximum import MaxInstant

        return MaxInstant(a=self, b=other)

    def before(self, other: Instant) -> Bool:
        """Whether this instant is strictly earlier than ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessThan

        return LessThan(a=self, b=other)

    def after(self, other: Instant) -> Bool:
        """Whether this instant is strictly later than ``other`` (→ ``Bool``)."""
        from fungeom.primitives.boolean.resolvers.comparison import LessThan

        return LessThan(a=other, b=self)
