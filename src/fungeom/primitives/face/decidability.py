"""Resolvability aliases for faces (oriented bounded patches)."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.face.value import FaceValue

type FaceResolvable = Resolvable[FaceValue]
"""A face decision that succeeded — carries the plane + region patch."""

type FaceUnresolvable = Unresolvable
"""A face decision that failed — carries the reason."""

type FaceDecision = Resolvability[FaceValue]
"""The result of deciding a ``Face``."""
