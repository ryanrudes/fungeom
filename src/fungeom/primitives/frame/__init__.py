from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.resolvers.known import KnownFrame
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame

# The root world frame, as a resolver (see ``Frame.world``).
Frame.world = KnownFrame(frame=WORLD_FRAME)

__all__ = ["Frame", "CoordinateFrame", "WORLD_FRAME"]
