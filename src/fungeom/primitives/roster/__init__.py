"""The ``Roster`` primitive — a set of entity keys (the support set of the nominal axis)."""

from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.roster.resolvers.literal import LiteralRoster
from fungeom.primitives.roster.value import RosterValue

# The empty roster, as a resolver (see ``Roster.empty``).
Roster.empty = LiteralRoster(keys=())

__all__ = ["Roster", "RosterValue"]
