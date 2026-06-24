"""The ``Coverage`` interface and its set algebra.

A coverage is a set of disjoint spans — the part of the timeline where something
is defined. It is where the union of *disjoint* intervals lives (an operation that
has no ``Interval`` answer), so its algebra is *total* where the interval algebra
was partial: :meth:`union` and :meth:`intersection` always succeed (the result may
just be empty). Sibling resolver types are imported lazily to keep module load
acyclic; the lower-layer ``Interval`` / ``Duration`` are imported normally.
"""

from __future__ import annotations

from typing import ClassVar

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.coverage.value import CoverageValue
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval


class Coverage(Resolver[CoverageValue]):
    """A deferred set of disjoint spans — where data exists on the timeline.

    Construct one with :meth:`of` (from a collection of intervals, normalized) or
    the :attr:`empty` constant; compose with :meth:`union` / :meth:`intersection` /
    :meth:`difference` (→ ``Coverage``), :meth:`total_duration` (→ ``Duration``),
    :meth:`hull` (→ ``Interval``), :meth:`gaps` (→ ``Coverage``), and the predicate
    :meth:`contains` (→ :class:`~fungeom.Bool`). ``resolve()`` yields a
    :class:`~fungeom.primitives.coverage.value.CoverageValue` (``Coverage.Value``).

    The set algebra is *total* — the union of disjoint spans is exactly what a
    coverage is for. The one *partial* operation is :meth:`hull`: an empty
    coverage has no bounding interval and is :class:`~fungeom.Unresolvable`.
    """

    type Value = CoverageValue
    """The resolved value type — a :class:`CoverageValue`."""

    empty: ClassVar[Coverage]
    """The empty coverage, as a resolver. (Assigned once ``LiteralCoverage`` exists.)"""

    @classmethod
    def of(cls, intervals: list[Interval] | tuple[Interval, ...]) -> Coverage:
        """A coverage spanning ``intervals`` (sorted and merged into a disjoint set)."""
        from fungeom.primitives.coverage.resolvers.literal import LiteralCoverage

        return LiteralCoverage(intervals=tuple(intervals))

    def union(self, other: Coverage) -> Coverage:
        """Everything covered by this *or* ``other``."""
        from fungeom.primitives.coverage.resolvers.union import CoverageUnion

        return CoverageUnion(a=self, b=other)

    def intersection(self, other: Coverage) -> Coverage:
        """Everything covered by this *and* ``other``."""
        from fungeom.primitives.coverage.resolvers.intersection import CoverageIntersection

        return CoverageIntersection(a=self, b=other)

    def difference(self, other: Coverage) -> Coverage:
        """Everything covered by this but *not* ``other`` (empty when ``other`` swallows it)."""
        from fungeom.primitives.coverage.resolvers.difference import CoverageDifference

        return CoverageDifference(a=self, b=other)

    def total_duration(self) -> Duration:
        """The summed length of every span (zero for empty coverage)."""
        from fungeom.primitives.coverage.resolvers.total_duration import CoverageTotalDuration

        return CoverageTotalDuration(coverage=self)

    def hull(self) -> Interval:
        """The smallest single interval containing all spans (Unresolvable if empty)."""
        from fungeom.primitives.coverage.resolvers.hull import CoverageHull

        return CoverageHull(coverage=self)

    def gaps(self) -> Coverage:
        """The holes between spans — the complement within the :meth:`hull`."""
        from fungeom.primitives.coverage.resolvers.gaps import CoverageGaps

        return CoverageGaps(coverage=self)

    def contains(self, instant: Instant | float) -> Bool:
        """Whether ``instant`` falls inside any covered span (→ ``Bool``)."""
        from fungeom.primitives.coverage.resolvers.contains import CoverageContains
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return CoverageContains(coverage=self, instant=as_instant_resolver(instant))
