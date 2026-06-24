"""Resolvability aliases for segments."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.segment.value import SegmentValue

type SegmentResolvable = Resolvable[SegmentValue]
"""A segment decision that succeeded — carries the finite segment."""

type SegmentUnresolvable = Unresolvable
"""A segment decision that failed — carries the reason."""

type SegmentDecision = Resolvability[SegmentValue]
"""The result of deciding a ``Segment``."""
