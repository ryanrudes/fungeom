"""The ``Frame2`` primitive — a tree of 2D coordinate frames."""

from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.frame2.resolvers.known import KnownFrame2
from fungeom.primitives.frame2.value import WORLD_FRAME2, CoordinateFrame2

# The root world frame, as a resolver (see ``Frame2.world``).
Frame2.world = KnownFrame2(frame=WORLD_FRAME2)

__all__ = ["Frame2", "CoordinateFrame2", "WORLD_FRAME2"]
