"""Resolvability aliases for 2D segments."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.segment2.value import Segment2Value

type Segment2Resolvable = Resolvable[Segment2Value]
"""A segment decision that succeeded — carries the finite segment."""

type Segment2Unresolvable = Unresolvable
"""A segment decision that failed — carries the reason."""

type Segment2Decision = Resolvability[Segment2Value]
"""The result of deciding a ``Segment2``."""
