"""Resolvability aliases for booleans."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable

type BoolResolvable = Resolvable[bool]
"""A boolean decision that succeeded — carries the truth value."""

type BoolUnresolvable = Unresolvable
"""A boolean decision that failed — carries the reason (e.g. an unresolvable operand)."""

type BoolDecision = Resolvability[bool]
"""The result of deciding a ``Bool``."""
