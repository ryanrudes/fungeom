"""Resolvability aliases for lines."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.line.value import LineValue

type LineResolvable = Resolvable[LineValue]
"""A line decision that succeeded — carries the oriented line."""

type LineUnresolvable = Unresolvable
"""A line decision that failed — carries the reason (e.g. coincident defining points)."""

type LineDecision = Resolvability[LineValue]
"""The result of deciding a ``Line``."""
