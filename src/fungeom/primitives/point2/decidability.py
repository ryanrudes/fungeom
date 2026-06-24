"""Resolvability aliases for 2D points."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.point2.value import Point2Value

type Point2Resolvable = Resolvable[Point2Value]
"""A point decision that succeeded — carries the world-anchored value."""

type Point2Unresolvable = Unresolvable
"""A point decision that failed — carries the reason."""

type Point2Decision = Resolvability[Point2Value]
"""The result of deciding a ``Point2``."""
