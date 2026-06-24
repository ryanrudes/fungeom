"""The ``Coverage`` primitive — a set of disjoint intervals (where data exists)."""

from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.resolvers.literal import LiteralCoverage
from fungeom.primitives.coverage.value import CoverageValue

# The empty coverage, as a resolver (see ``Coverage.empty``).
Coverage.empty = LiteralCoverage(intervals=())

__all__ = ["Coverage", "CoverageValue"]
