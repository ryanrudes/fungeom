"""The interval *value*: a contiguous span of time.

An :class:`IntervalValue` is a closed span ``[start, end]`` of master-clock
seconds with ``start ≤ end``. The value type guarantees the invariant — an
interval whose end precedes its start cannot exist. The deferred counterpart, an
``Interval`` that resolves to one, lives in
:mod:`fungeom.primitives.interval.resolvers`. Unlike space, the timeline is
*ordered*, which is exactly what makes an interval (and its set algebra) possible.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntervalValue:
    """A closed span ``[start, end]`` of seconds, with ``start ≤ end``."""

    start: float
    end: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", float(self.start))
        object.__setattr__(self, "end", float(self.end))
        if self.end < self.start:
            raise ValueError(f"interval end ({self.end:g}) precedes start ({self.start:g})")

    @property
    def duration(self) -> float:
        """The length of the span in seconds (always ≥ 0)."""
        return self.end - self.start

    def __repr__(self) -> str:
        return f"IntervalValue([{self.start:g}, {self.end:g}])"
