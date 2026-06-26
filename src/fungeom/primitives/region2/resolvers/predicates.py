"""Region-region relational predicates (→ Bool): ``intersects`` and ``contains_region``.

Both delegate to GEOS via the shapely bridge. They are *not* cleanly composable from the
area-based boolean ops (which drop measure-zero touches), so they earn their own place: a
boundary-only contact still counts as intersecting, and containment is the closed ⊆ (a region
contains another even when their boundaries touch).
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.shapely_bridge import to_shapely


@dataclass(frozen=True, eq=False)
class Region2Intersects(Bool):
    """Whether ``a`` and ``b`` share any point (boundary contact included). Total."""

    a: Region2
    b: Region2

    def _decide(self) -> BoolDecision:
        match self.a.decide(), self.b.decide():
            case (Resolvable(ra), Resolvable(rb)):
                return Resolvable(bool(to_shapely(ra).intersects(to_shapely(rb))))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class Region2ContainsRegion(Bool):
    """Whether ``a`` fully contains ``b`` (closed ⊆ — boundary contact still counts). Total."""

    a: Region2
    b: Region2

    def _decide(self) -> BoolDecision:
        match self.a.decide(), self.b.decide():
            case (Resolvable(ra), Resolvable(rb)):
                return Resolvable(bool(to_shapely(ra).covers(to_shapely(rb))))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
