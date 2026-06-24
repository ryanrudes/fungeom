from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.boolean.resolvers.literal import LiteralBool

# The truth-value constants, as resolvers (see ``Bool.true`` / ``Bool.false``).
Bool.true = LiteralBool(value=True)
Bool.false = LiteralBool(value=False)

__all__ = ["Bool"]
