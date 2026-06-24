"""Resolvability aliases for 2D rays."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.ray2.value import Ray2Value

type Ray2Resolvable = Resolvable[Ray2Value]
"""A ray decision that succeeded — carries the half-line."""

type Ray2Unresolvable = Unresolvable
"""A ray decision that failed — carries the reason."""

type Ray2Decision = Resolvability[Ray2Value]
"""The result of deciding a ``Ray2``."""
