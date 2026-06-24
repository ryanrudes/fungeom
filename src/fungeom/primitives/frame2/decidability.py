"""Resolvability aliases for 2D coordinate frames."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.frame2.value import CoordinateFrame2

type CoordinateFrame2Resolvable = Resolvable[CoordinateFrame2]
"""A frame decision that succeeded — carries the world-grounded frame."""

type CoordinateFrame2Unresolvable = Unresolvable
"""A frame decision that failed — carries the reason."""

type CoordinateFrame2Decision = Resolvability[CoordinateFrame2]
"""The result of deciding a ``Frame2``."""
