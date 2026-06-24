"""Resolvability aliases for intervals."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.interval.value import IntervalValue

type IntervalResolvable = Resolvable[IntervalValue]
"""An interval decision that succeeded — carries the span."""

type IntervalUnresolvable = Unresolvable
"""An interval decision that failed — carries the reason (e.g. end before start)."""

type IntervalDecision = Resolvability[IntervalValue]
"""The result of deciding an ``Interval``."""
