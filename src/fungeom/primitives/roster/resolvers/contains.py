"""Membership of a key in a roster — resolving to a ``Bool``.

Resolves into a :class:`~fungeom.Bool` but is built from a ``Roster`` and a key, so it
lives under ``roster`` (which already depends on ``boolean``). The nominal-axis mirror
of :class:`~fungeom.primitives.coverage.resolvers.contains.CoverageContains`.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.roster.resolvers.base import Roster


@dataclass(frozen=True, eq=False)
class RosterContains(Bool):
    """Whether ``key`` is a member of ``roster``."""

    roster: Roster
    key: Hashable

    def _decide(self) -> BoolDecision:
        match self.roster.decide():
            case Resolvable(value):
                return Resolvable(self.key in value)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
