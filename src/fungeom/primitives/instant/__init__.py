from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.instant.resolvers.literal import LiteralInstant

# The master-clock origin, as a resolver (see ``Instant.epoch``).
Instant.epoch = LiteralInstant(seconds=0.0)

__all__ = ["Instant"]
