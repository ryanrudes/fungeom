"""Resolvability aliases for coverages."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.coverage.value import CoverageValue

type CoverageResolvable = Resolvable[CoverageValue]
"""A coverage decision that succeeded — carries the disjoint set of spans."""

type CoverageUnresolvable = Unresolvable
"""A coverage decision that failed — carries the reason."""

type CoverageDecision = Resolvability[CoverageValue]
"""The result of deciding a ``Coverage``."""
