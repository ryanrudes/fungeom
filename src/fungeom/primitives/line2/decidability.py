"""Resolvability aliases for 2D lines."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.line2.value import Line2Value

type Line2Resolvable = Resolvable[Line2Value]
"""A line decision that succeeded — carries the oriented line."""

type Line2Unresolvable = Unresolvable
"""A line decision that failed — carries the reason (e.g. coincident defining points)."""

type Line2Decision = Resolvability[Line2Value]
"""The result of deciding a ``Line2``."""
