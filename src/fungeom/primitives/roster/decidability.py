"""Resolvability aliases for rosters."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.roster.value import RosterValue

type RosterResolvable = Resolvable[RosterValue]
"""A roster decision that succeeded — carries the set of keys."""

type RosterUnresolvable = Unresolvable
"""A roster decision that failed — carries the reason."""

type RosterDecision = Resolvability[RosterValue]
"""The result of deciding a ``Roster``."""
