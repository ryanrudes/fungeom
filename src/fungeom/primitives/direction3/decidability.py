"""Resolvability aliases for directions."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.direction3.value import Direction3Value

type Direction3Resolvable = Resolvable[Direction3Value]
"""A direction decision that succeeded — carries the unit direction."""

type Direction3Unresolvable = Unresolvable
"""A direction decision that failed — carries the reason."""

type Direction3Decision = Resolvability[Direction3Value]
"""The result of deciding a ``Direction3``."""
