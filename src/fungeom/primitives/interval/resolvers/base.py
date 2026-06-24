"""The ``Interval`` interface and its set algebra.

An interval is a contiguous, ordered span on the timeline — the simplest
primitive that exists only because time (unlike space) is *totally ordered*. You
build one from two instants (or a start plus a duration) and compose with span
queries (:meth:`start`, :meth:`end`, :meth:`duration`, :meth:`lerp`) and the set
algebra (:meth:`intersection`, :meth:`hull`, :meth:`clamp`). Sibling resolver
types are imported lazily to keep module load acyclic; the lower-layer
``Instant`` / ``Duration`` are imported normally.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.scalar.resolvers.base import Scalar


class Interval(Resolver[IntervalValue]):
    """A deferred contiguous span ``[start, end]`` of master-clock seconds.

    Construct one with :meth:`between`, :meth:`of`, :meth:`point`, or
    :meth:`around`; compose with :meth:`start` / :meth:`end` (→ ``Instant``),
    :meth:`duration` (→ ``Duration``), :meth:`lerp` / :meth:`midpoint`
    (→ ``Instant``), :meth:`intersection` / :meth:`hull` (→ ``Interval``),
    :meth:`clamp` (→ ``Instant``), the rigid/symmetric reshapings
    :meth:`shifted` / :meth:`expanded` (→ ``Interval``), and the predicates
    :meth:`contains` / :meth:`overlaps` (→ :class:`~fungeom.Bool`). ``resolve()``
    yields an :class:`~fungeom.primitives.interval.value.IntervalValue`
    (``Interval.Value``).

    Two operations are *partial*: :meth:`between` (and the constructors that build
    on it) is :class:`~fungeom.Unresolvable` when the end precedes the start, and
    :meth:`intersection` is ``Unresolvable`` when the two spans are disjoint — the
    order-structured analog of the centroid of no points.
    """

    type Value = IntervalValue
    """The resolved value type — an :class:`IntervalValue`."""

    @classmethod
    def between(cls, start: Instant | float, end: Instant | float) -> Interval:
        """The span from ``start`` to ``end`` (Unresolvable if ``end`` precedes ``start``)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver
        from fungeom.primitives.interval.resolvers.between import BetweenInterval

        return BetweenInterval(start_at=as_instant_resolver(start), end_at=as_instant_resolver(end))

    @classmethod
    def of(cls, start: Instant | float, duration: Duration | float) -> Interval:
        """The span starting at ``start`` and lasting ``duration`` (Unresolvable if negative)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        anchor = as_instant_resolver(start)
        return cls.between(anchor, anchor.shifted_by(Duration.of(duration)))

    @classmethod
    def point(cls, instant: Instant | float) -> Interval:
        """The degenerate, zero-length span ``[instant, instant]``."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        anchor = as_instant_resolver(instant)
        return cls.between(anchor, anchor)

    @classmethod
    def around(cls, center: Instant | float, radius: Duration | float) -> Interval:
        """The span ``[center - radius, center + radius]`` (Unresolvable if ``radius`` is negative)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        anchor = as_instant_resolver(center)
        reach = Duration.of(radius)
        return cls.between(anchor.shifted_by(-reach), anchor.shifted_by(reach))

    def start(self) -> Instant:
        """The starting instant of this span."""
        from fungeom.primitives.interval.resolvers.endpoint import IntervalStart

        return IntervalStart(interval=self)

    def end(self) -> Instant:
        """The ending instant of this span."""
        from fungeom.primitives.interval.resolvers.endpoint import IntervalEnd

        return IntervalEnd(interval=self)

    def duration(self) -> Duration:
        """The length of this span (``end - start``, always ≥ 0)."""
        return self.start().duration_to(self.end())

    def lerp(self, t: float | Scalar) -> Instant:
        """The instant a fraction ``t`` of the way across this span (``t=0`` start, ``t=1`` end)."""
        return self.start().lerp(self.end(), t)

    def midpoint(self) -> Instant:
        """The instant at the center of this span."""
        return self.lerp(0.5)

    def intersection(self, other: Interval) -> Interval:
        """The overlap of this span and ``other`` (Unresolvable if they are disjoint)."""
        from fungeom.primitives.interval.resolvers.intersection import IntervalIntersection

        return IntervalIntersection(a=self, b=other)

    def hull(self, other: Interval) -> Interval:
        """The smallest span containing both this one and ``other`` (the convex hull)."""
        from fungeom.primitives.interval.resolvers.hull import IntervalHull

        return IntervalHull(a=self, b=other)

    def clamp(self, instant: Instant | float) -> Instant:
        """``instant`` clamped into this span (returns the nearest instant within ``[start, end]``)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver
        from fungeom.primitives.interval.resolvers.clamp import IntervalClamp

        return IntervalClamp(interval=self, instant=as_instant_resolver(instant))

    def shifted(self, by: Duration | float) -> Interval:
        """This whole span translated later by ``by`` (earlier if negative).

        Always valid — a rigid shift preserves the ordering of the endpoints.
        """
        offset = Duration.of(by)
        return Interval.between(self.start().shifted_by(offset), self.end().shifted_by(offset))

    def expanded(self, by: Duration | float) -> Interval:
        """This span grown by ``by`` at *each* end (shrunk if ``by`` is negative).

        Unresolvable when a negative ``by`` shrinks the span past empty (the end
        would precede the start) — the partiality is inherited from :meth:`between`.
        """
        reach = Duration.of(by)
        return Interval.between(self.start().shifted_by(-reach), self.end().shifted_by(reach))

    def contains(self, instant: Instant | float) -> Bool:
        """Whether ``instant`` lies within this closed span (→ ``Bool``)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver
        from fungeom.primitives.interval.resolvers.contains import IntervalContains

        return IntervalContains(interval=self, instant=as_instant_resolver(instant))

    def overlaps(self, other: Interval) -> Bool:
        """Whether this span shares any instant with ``other`` (→ ``Bool``; touching counts)."""
        from fungeom.primitives.interval.resolvers.overlaps import IntervalOverlaps

        return IntervalOverlaps(a=self, b=other)
