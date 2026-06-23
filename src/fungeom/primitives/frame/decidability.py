"""Resolvability aliases for coordinate frames.

These name the two outcomes of deciding a ``Frame``, so that
resolver signatures and ``match`` arms read in domain terms. Failures are not
type-tagged (``Unresolvable`` carries only a reason), so ``...Unresolvable`` is
the shared :class:`Unresolvable`.
"""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.frame.value import CoordinateFrame

type CoordinateFrameResolvable = Resolvable[CoordinateFrame]
"""A frame decision that succeeded — carries the world-grounded frame."""

type CoordinateFrameUnresolvable = Unresolvable
"""A frame decision that failed — carries the reason."""

type CoordinateFrameDecision = Resolvability[CoordinateFrame]
"""The result of deciding a ``Frame``."""
