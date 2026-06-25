"""Resolvability aliases for 2D regions."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.region2.value import Region2Value

type Region2Resolvable = Resolvable[Region2Value]
"""A region decision that succeeded — carries the polygonal area."""

type Region2Unresolvable = Unresolvable
"""A region decision that failed — carries the reason."""

type Region2Decision = Resolvability[Region2Value]
"""The result of deciding a ``Region2``."""
