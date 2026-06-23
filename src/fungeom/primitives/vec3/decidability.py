"""Resolvability aliases for vectors."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.vec3.value import Float3

type Vec3Resolvable = Resolvable[Float3]
"""A vector decision that succeeded — carries the computed vector."""

type Vec3Unresolvable = Unresolvable
"""A vector decision that failed — carries the reason."""

type Vec3Decision = Resolvability[Float3]
"""The result of deciding a ``Vec3``."""
