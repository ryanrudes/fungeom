"""Resolvability aliases for points."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.point3.value import Point3Value

type Point3Resolvable = Resolvable[Point3Value]
"""A point decision that succeeded — carries the world-anchored value."""

type Point3Unresolvable = Unresolvable
"""A point decision that failed — carries the reason."""

type Point3Decision = Resolvability[Point3Value]
"""The result of deciding a ``Point3``."""
