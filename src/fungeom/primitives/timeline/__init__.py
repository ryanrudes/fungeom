from fungeom.primitives.timeline.resolvers.base import Timeline
from fungeom.primitives.timeline.resolvers.known import KnownTimeline
from fungeom.primitives.timeline.value import MASTER_CLOCK, Clock

# The root master clock, as a resolver (see ``Timeline.master``).
Timeline.master = KnownTimeline(clock=MASTER_CLOCK)

__all__ = ["Timeline", "Clock", "MASTER_CLOCK"]
