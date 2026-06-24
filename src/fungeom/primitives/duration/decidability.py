"""Resolvability aliases for durations."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable

type DurationResolvable = Resolvable[float]
"""A duration decision that succeeded — carries the elapsed seconds."""

type DurationUnresolvable = Unresolvable
"""A duration decision that failed — carries the reason."""

type DurationDecision = Resolvability[float]
"""The result of deciding a ``Duration``."""
