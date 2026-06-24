"""Resolvability aliases for instants."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable

type InstantResolvable = Resolvable[float]
"""An instant decision that succeeded — carries the master-clock seconds."""

type InstantUnresolvable = Unresolvable
"""An instant decision that failed — carries the reason."""

type InstantDecision = Resolvability[float]
"""The result of deciding an ``Instant``."""
