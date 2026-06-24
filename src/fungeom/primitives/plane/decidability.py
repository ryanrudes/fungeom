"""Resolvability aliases for planes."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.plane.value import PlaneValue

type PlaneResolvable = Resolvable[PlaneValue]
"""A plane decision that succeeded — carries the oriented plane."""

type PlaneUnresolvable = Unresolvable
"""A plane decision that failed — carries the reason (e.g. collinear defining points)."""

type PlaneDecision = Resolvability[PlaneValue]
"""The result of deciding a ``Plane``."""
