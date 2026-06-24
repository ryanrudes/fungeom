"""Resolvability aliases for rays."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.ray.value import RayValue

type RayResolvable = Resolvable[RayValue]
"""A ray decision that succeeded — carries the half-line."""

type RayUnresolvable = Unresolvable
"""A ray decision that failed — carries the reason (e.g. coincident origin and target)."""

type RayDecision = Resolvability[RayValue]
"""The result of deciding a ``Ray``."""
