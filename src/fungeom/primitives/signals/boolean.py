"""``BoolSignal`` — a truth value that varies over time (a whole-timeline predicate).

The contact-spine keystone. Unlike the sampled signals, a ``BoolSignal`` is *not* a
``SampledSeries`` — a boolean cannot be linearly interpolated. It is a **temporal predicate**:
a value (:class:`BoolSeries`) carrying *where it is defined* (a support ``Coverage``) and
*where it holds* (a true ``Coverage`` ⊆ support). It is born from thresholding a
``ScalarSignal`` — the true-set is read off the linear interpolant's **exact sub-sample
crossings** (per the decidable ethos, not hold-based sample-grid spans) — and composes under a
strict three-valued logic (``& | ~``): a query in a gap is ``Unresolvable`` (undefined), not
``False``, keeping occluded contact honest. ``when_true`` → the contact ``Coverage``,
``first_true`` → the touchdown ``Instant``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.coverage.decidability import CoverageDecision
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue, intersect, subtract
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.signals.scalar import ScalarSignal
from fungeom.primitives.signals.series import SampledSeries


@dataclass(frozen=True)
class BoolSeries:
    """A temporal predicate: where it is *defined* (``support``) and where it *holds* (``true``).

    Three-valued by construction — at an instant the predicate is *true* (in ``true``),
    *false* (in ``support`` but not ``true``), or *undefined* (outside ``support``). ``true`` is
    always a subset of ``support``.
    """

    support: CoverageValue
    true: CoverageValue

    def holds_at(self, t: float) -> bool | None:
        """``True`` / ``False`` where defined, ``None`` (undefined) outside the support."""
        if not _contains(self.support, t):
            return None
        return _contains(self.true, t)

    def __repr__(self) -> str:
        return f"BoolSeries(true over {self.true}, defined over {self.support})"


def _contains(coverage: CoverageValue, t: float) -> bool:
    """Whether instant ``t`` lies in some span of ``coverage`` (closed)."""
    return any(span.start <= t <= span.end for span in coverage.intervals)


def threshold_true(series: SampledSeries[float], threshold: float, satisfies: Callable[[float], bool]) -> CoverageValue:
    """The spans where ``series``' linear interpolant satisfies ``satisfies`` — exact crossings.

    Each segment between same-span samples is split at its exact threshold crossing; the open
    sub-pieces are classified by their midpoint. A fully-isolated sample contributes a
    degenerate point when it satisfies. Never crosses a gap.
    """
    times, values = series.times, series.values
    spans = series.support.intervals
    n = len(times)

    def connected(i: int, j: int) -> bool:
        return any(span.start <= float(times[i]) and float(times[j]) <= span.end for span in spans)

    intervals: list[IntervalValue] = []
    for i in range(n - 1):
        if not connected(i, i + 1):
            continue
        t0, t1 = float(times[i]), float(times[i + 1])
        v0, v1 = float(values[i]), float(values[i + 1])
        cuts = [0.0, 1.0]
        if v0 != v1:
            crossing = (threshold - v0) / (v1 - v0)
            if 0.0 < crossing < 1.0:
                cuts = [0.0, crossing, 1.0]
        for a, b in zip(cuts, cuts[1:]):
            if satisfies(v0 + 0.5 * (a + b) * (v1 - v0)):
                intervals.append(IntervalValue(start=t0 + a * (t1 - t0), end=t0 + b * (t1 - t0)))
    for i in range(n):
        isolated = not (i > 0 and connected(i - 1, i)) and not (i < n - 1 and connected(i, i + 1))
        if isolated and satisfies(float(values[i])):
            intervals.append(IntervalValue(start=float(times[i]), end=float(times[i])))
    return CoverageValue(tuple(intervals))


class BoolSignal(Resolver[BoolSeries]):
    """A deferred truth value over time — a three-valued temporal predicate.

    Born from a ``ScalarSignal`` threshold (``lt`` / ``le`` / ``gt`` / ``ge``); composed with
    :meth:`and_` / :meth:`or_` / :meth:`not_` (``& | ~``). Read it with :meth:`at` (→ ``Bool``,
    Unresolvable in a gap), :meth:`when_true` / :meth:`when_false` (→ ``Coverage``),
    :meth:`first_true` (→ ``Instant``), and :meth:`support` (→ ``Coverage``).
    """

    type Value = BoolSeries
    """The resolved value type — a :class:`BoolSeries` (support + true spans)."""

    def at(self, instant: Instant | float) -> Bool:
        """The truth value at ``instant`` (→ ``Bool``; Unresolvable where undefined — a gap)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _BoolSignalAt(signal=self, instant=as_instant_resolver(instant))

    def support(self) -> Coverage:
        """Where this predicate is defined (→ ``Coverage``)."""
        return _BoolSignalSupport(signal=self)

    def when_true(self) -> Coverage:
        """The spans where the predicate holds (→ ``Coverage``) — e.g. the contact intervals."""
        return _BoolSignalWhen(signal=self, negate=False)

    def when_false(self) -> Coverage:
        """The defined spans where the predicate does *not* hold (→ ``Coverage``)."""
        return _BoolSignalWhen(signal=self, negate=True)

    def first_true(self) -> Instant:
        """The earliest instant the predicate holds (→ ``Instant``; Unresolvable if never)."""
        return _BoolSignalFirstTrue(signal=self)

    def and_(self, other: BoolSignal) -> BoolSignal:
        """Strict conjunction — defined only where *both* are (→ ``BoolSignal``)."""
        return _CombinedBoolSignal(a=self, b=other, op="and")

    def or_(self, other: BoolSignal) -> BoolSignal:
        """Strict disjunction — defined only where *both* are (→ ``BoolSignal``)."""
        return _CombinedBoolSignal(a=self, b=other, op="or")

    def not_(self) -> BoolSignal:
        """Negation — same support, true ↔ false (→ ``BoolSignal``)."""
        return _NotBoolSignal(source=self)

    def __and__(self, other: BoolSignal) -> BoolSignal:
        return self.and_(other)

    def __or__(self, other: BoolSignal) -> BoolSignal:
        return self.or_(other)

    def __invert__(self) -> BoolSignal:
        return self.not_()


@dataclass(frozen=True, eq=False)
class _ThresholdBoolSignal(BoolSignal):
    """A ``ScalarSignal`` thresholded against a constant — the exact-crossing true-set."""

    source: ScalarSignal
    threshold: float
    satisfies: Callable[[float], bool]

    def _decide(self) -> Resolvability[BoolSeries]:
        match self.source.decide():
            case Resolvable(series):
                true = threshold_true(series, self.threshold, self.satisfies)
                return Resolvable(BoolSeries(support=series.support, true=true))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _NotBoolSignal(BoolSignal):
    source: BoolSignal

    def _decide(self) -> Resolvability[BoolSeries]:
        match self.source.decide():
            case Resolvable(series):
                true = CoverageValue(subtract(series.support.intervals, series.true.intervals))
                return Resolvable(BoolSeries(support=series.support, true=true))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _CombinedBoolSignal(BoolSignal):
    a: BoolSignal
    b: BoolSignal
    op: str

    def _decide(self) -> Resolvability[BoolSeries]:
        decided_a, decided_b = self.a.decide(), self.b.decide()
        if isinstance(decided_a, Unresolvable):
            return decided_a
        if isinstance(decided_b, Unresolvable):
            return decided_b
        support = CoverageValue(intersect(decided_a.value.support.intervals, decided_b.value.support.intervals))
        if self.op == "and":
            true = intersect(decided_a.value.true.intervals, decided_b.value.true.intervals)
        else:  # or
            union = CoverageValue(decided_a.value.true.intervals + decided_b.value.true.intervals)
            true = intersect(union.intervals, support.intervals)
        return Resolvable(BoolSeries(support=support, true=CoverageValue(intersect(true, support.intervals))))


@dataclass(frozen=True, eq=False)
class _BoolSignalAt(Bool):
    signal: BoolSignal
    instant: Instant

    def _decide(self) -> BoolDecision:
        match self.signal.decide(), self.instant.decide():
            case (Resolvable(series), Resolvable(t)):
                verdict = series.holds_at(float(t))
                if verdict is None:
                    return Unresolvable(f"the predicate is undefined at t={float(t):g}s (a gap)")
                return Resolvable(verdict)
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BoolSignalSupport(Coverage):
    signal: BoolSignal

    def _decide(self) -> CoverageDecision:
        match self.signal.decide():
            case Resolvable(series):
                return Resolvable(series.support)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BoolSignalWhen(Coverage):
    signal: BoolSignal
    negate: bool

    def _decide(self) -> CoverageDecision:
        match self.signal.decide():
            case Resolvable(series):
                if self.negate:
                    return Resolvable(CoverageValue(subtract(series.support.intervals, series.true.intervals)))
                return Resolvable(series.true)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BoolSignalFirstTrue(Instant):
    signal: BoolSignal

    def _decide(self) -> InstantDecision:
        match self.signal.decide():
            case Resolvable(series):
                if series.true.is_empty:
                    return Unresolvable("the predicate is never true")
                return Resolvable(series.true.intervals[0].start)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
