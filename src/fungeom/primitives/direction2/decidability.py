"""Resolvability aliases for 2D directions."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.direction2.value import Direction2Value

type Direction2Resolvable = Resolvable[Direction2Value]
"""A direction decision that succeeded — carries the unit direction."""

type Direction2Unresolvable = Unresolvable
"""A direction decision that failed — carries the reason (e.g. the zero vector)."""

type Direction2Decision = Resolvability[Direction2Value]
"""The result of deciding a ``Direction2``."""
