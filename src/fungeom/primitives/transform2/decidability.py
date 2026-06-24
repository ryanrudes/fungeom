"""Resolvability aliases for 2D rigid transforms."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.transform2.value import RigidTransform2

type RigidTransform2Resolvable = Resolvable[RigidTransform2]
"""A transform decision that succeeded — carries the rigid transform."""

type RigidTransform2Unresolvable = Unresolvable
"""A transform decision that failed — carries the reason."""

type RigidTransform2Decision = Resolvability[RigidTransform2]
"""The result of deciding a ``Transform2``."""
