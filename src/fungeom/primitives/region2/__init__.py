"""The ``Region2`` primitive — a bounded planar region (the 2D spatial sibling of ``Coverage``)."""

from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.resolvers.literal import LiteralRegion2
from fungeom.primitives.region2.value import Region2Value

# The empty region, as a resolver (see ``Region2.empty``).
Region2.empty = LiteralRegion2(value=Region2Value(rings=()))

__all__ = ["Region2", "Region2Value"]
