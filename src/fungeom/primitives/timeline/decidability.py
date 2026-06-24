"""Resolvability aliases for timelines."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.timeline.value import Clock

type TimelineResolvable = Resolvable[Clock]
"""A timeline decision that succeeded — carries the master-grounded clock."""

type TimelineUnresolvable = Unresolvable
"""A timeline decision that failed — carries the reason (e.g. an un-synced clock)."""

type TimelineDecision = Resolvability[Clock]
"""The result of deciding a ``Timeline``."""
