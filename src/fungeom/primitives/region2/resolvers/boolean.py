"""The boolean region algebra — ``union`` / ``intersection`` / ``difference`` (general, via GEOS).

Each op converts both operands to shapely geometries, runs the GEOS boolean, and converts back —
so the algebra is **general** (arbitrary simple polygons, holes, multipolygons) and **total**:
given two resolvable regions the result is always a valid region (possibly empty). The only
partiality is propagation — an ``Unresolvable`` operand (a region built from an occluded marker)
makes the result ``Unresolvable``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.shapely_bridge import from_shapely, to_shapely
from fungeom.primitives.region2.value import Region2Value


def _binary(a: Region2, b: Region2, combine: Callable[[Region2Value, Region2Value], Region2Value]) -> Region2Decision:
    """Decide both operands, then combine their values — propagating any ``Unresolvable``."""
    decided_a, decided_b = a.decide(), b.decide()
    if isinstance(decided_a, Unresolvable):
        return decided_a
    if isinstance(decided_b, Unresolvable):
        return decided_b
    return Resolvable(combine(decided_a.value, decided_b.value))


@dataclass(frozen=True, eq=False)
class UnionRegion2(Region2):
    """The union of two regions (→ ``Region2``; disjoint parts become a multipolygon)."""

    a: Region2
    b: Region2

    def _decide(self) -> Region2Decision:
        return _binary(self.a, self.b, lambda ra, rb: from_shapely(to_shapely(ra).union(to_shapely(rb))))


@dataclass(frozen=True, eq=False)
class IntersectionRegion2(Region2):
    """The overlap of two regions (→ ``Region2``; empty if they do not meet in area)."""

    a: Region2
    b: Region2

    def _decide(self) -> Region2Decision:
        return _binary(self.a, self.b, lambda ra, rb: from_shapely(to_shapely(ra).intersection(to_shapely(rb))))


@dataclass(frozen=True, eq=False)
class DifferenceRegion2(Region2):
    """``a`` minus ``b`` (→ ``Region2``; a contained ``b`` is punched out as a hole)."""

    a: Region2
    b: Region2

    def _decide(self) -> Region2Decision:
        return _binary(self.a, self.b, lambda ra, rb: from_shapely(to_shapely(ra).difference(to_shapely(rb))))


@dataclass(frozen=True, eq=False)
class SymmetricDifferenceRegion2(Region2):
    """The symmetric difference of two regions (→ ``Region2``; the area in exactly one of them)."""

    a: Region2
    b: Region2

    def _decide(self) -> Region2Decision:
        return _binary(self.a, self.b, lambda ra, rb: from_shapely(to_shapely(ra).symmetric_difference(to_shapely(rb))))
