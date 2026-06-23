"""Resolvability aliases for rigid transforms."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.transform.value import RigidTransform

type RigidTransformResolvable = Resolvable[RigidTransform]
"""A transform decision that succeeded — carries the computed transform."""

type RigidTransformUnresolvable = Unresolvable
"""A transform decision that failed — carries the reason."""

type RigidTransformDecision = Resolvability[RigidTransform]
"""The result of deciding a ``Transform``."""
