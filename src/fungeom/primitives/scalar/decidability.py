"""Resolvability aliases for scalars."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable

type ScalarResolvable = Resolvable[float]
"""A scalar decision that succeeded — carries the computed number."""

type ScalarUnresolvable = Unresolvable
"""A scalar decision that failed — carries the reason (e.g. division by zero)."""

type ScalarDecision = Resolvability[float]
"""The result of deciding a ``Scalar``."""
