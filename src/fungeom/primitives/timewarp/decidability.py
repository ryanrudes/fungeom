"""Resolvability aliases for time warps."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.timewarp.value import PiecewiseLinearWarp

type TimeWarpResolvable = Resolvable[PiecewiseLinearWarp]
"""A time-warp decision that succeeded — carries the piecewise-linear warp."""

type TimeWarpUnresolvable = Unresolvable
"""A time-warp decision that failed — carries the reason (e.g. non-monotonic knots)."""

type TimeWarpDecision = Resolvability[PiecewiseLinearWarp]
"""The result of deciding a ``TimeWarp``."""
