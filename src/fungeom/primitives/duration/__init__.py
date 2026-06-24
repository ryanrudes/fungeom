from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.duration.resolvers.literal import LiteralDuration

# The zero duration, as a resolver (see ``Duration.zero``).
Duration.zero = LiteralDuration(value=0.0)

__all__ = ["Duration"]
