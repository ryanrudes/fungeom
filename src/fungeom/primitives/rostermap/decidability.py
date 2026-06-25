"""Resolvability aliases for roster maps."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.rostermap.value import KeyCorrespondence

type RosterMapResolvable = Resolvable[KeyCorrespondence]
"""A roster-map decision that succeeded — carries the key correspondence."""

type RosterMapUnresolvable = Unresolvable
"""A roster-map decision that failed — carries the reason (e.g. a non-injective inverse)."""

type RosterMapDecision = Resolvability[KeyCorrespondence]
"""The result of deciding a ``RosterMap``."""
