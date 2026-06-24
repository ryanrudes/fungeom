"""Resolvability aliases for time maps."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.timemap.value import AffineTimeMap

type TimeMapResolvable = Resolvable[AffineTimeMap]
"""A time-map decision that succeeded — carries the affine map."""

type TimeMapUnresolvable = Unresolvable
"""A time-map decision that failed — carries the reason (e.g. a non-invertible map)."""

type TimeMapDecision = Resolvability[AffineTimeMap]
"""The result of deciding a ``TimeMap``."""
