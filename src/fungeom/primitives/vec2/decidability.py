"""Resolvability aliases for 2D vectors."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.vec2.value import Float2

type Vec2Resolvable = Resolvable[Float2]
"""A 2D-vector decision that succeeded — carries the computed vector."""

type Vec2Unresolvable = Unresolvable
"""A 2D-vector decision that failed — carries the reason."""

type Vec2Decision = Resolvability[Float2]
"""The result of deciding a ``Vec2``."""
