"""The coverage *value*: a set of disjoint intervals — where data *exists*.

A :class:`CoverageValue` is a finite union of disjoint, sorted spans. It is the
honest answer to "over what part of the timeline is something defined", and it is
where the union of *disjoint* intervals — which is not itself an ``Interval`` —
finally has a home. Construction always **normalizes**: the spans are sorted and
any that overlap or touch are merged, so a coverage value is canonical (and two
equal coverages compare equal).

This module also exposes the set-algebra helpers (:func:`normalize`,
:func:`intersect`, :func:`gaps`) the coverage resolvers are built from.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from fungeom.primitives.interval.value import IntervalValue


def normalize(intervals: Iterable[IntervalValue]) -> tuple[IntervalValue, ...]:
    """Sort spans and merge any that overlap or touch into a canonical disjoint set."""
    ordered = sorted(intervals, key=lambda iv: (iv.start, iv.end))
    merged: list[IntervalValue] = []
    for span in ordered:
        if merged and span.start <= merged[-1].end:
            last = merged[-1]
            if span.end > last.end:
                merged[-1] = IntervalValue(start=last.start, end=span.end)
        else:
            merged.append(span)
    return tuple(merged)


def intersect(a: tuple[IntervalValue, ...], b: tuple[IntervalValue, ...]) -> tuple[IntervalValue, ...]:
    """The overlap of two *normalized* coverages (closed: a shared endpoint counts)."""
    out: list[IntervalValue] = []
    i = j = 0
    while i < len(a) and j < len(b):
        low = max(a[i].start, b[j].start)
        high = min(a[i].end, b[j].end)
        if low <= high:
            out.append(IntervalValue(start=low, end=high))
        if a[i].end <= b[j].end:
            i += 1
        else:
            j += 1
    return tuple(out)


def gaps(intervals: tuple[IntervalValue, ...]) -> tuple[IntervalValue, ...]:
    """The spans *between* the (normalized) intervals — the holes within their hull."""
    return tuple(IntervalValue(start=intervals[k].end, end=intervals[k + 1].start) for k in range(len(intervals) - 1))


def subtract(a: tuple[IntervalValue, ...], b: tuple[IntervalValue, ...]) -> tuple[IntervalValue, ...]:
    """``a`` with everything in (normalized) ``b`` carved out — closed, so shared endpoints survive.

    Like :func:`gaps`, this works in closed-interval arithmetic: removing a span
    leaves its boundary instants behind (point-overlaps are measure-zero), keeping
    every result a closed ``IntervalValue``.
    """
    out: list[IntervalValue] = []
    for span in a:
        cursor, end = span.start, span.end
        for hole in b:
            if hole.end <= cursor:
                continue
            if hole.start >= end:
                break
            if hole.start > cursor:
                out.append(IntervalValue(start=cursor, end=hole.start))
            cursor = max(cursor, hole.end)
            if cursor >= end:
                break
        if cursor < end:
            out.append(IntervalValue(start=cursor, end=end))
    return tuple(out)


@dataclass(frozen=True)
class CoverageValue:
    """A canonical (sorted, disjoint, merged) union of intervals."""

    intervals: tuple[IntervalValue, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "intervals", normalize(self.intervals))

    @property
    def total_duration(self) -> float:
        """The summed length of every span (0 for empty coverage)."""
        return sum((span.duration for span in self.intervals), 0.0)

    @property
    def is_empty(self) -> bool:
        """Whether this coverage contains no spans."""
        return not self.intervals

    def __repr__(self) -> str:
        spans = ", ".join(f"[{s.start:g}, {s.end:g}]" for s in self.intervals)
        return f"CoverageValue([{spans}])"
