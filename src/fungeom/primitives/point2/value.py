"""The point2 *value*: a framed 2D position.

A :class:`Point2Value` is the planar sibling of
:class:`~fungeom.values.Point3Value` — a position together with the 2D coordinate frame
it is expressed in. The deferred counterpart, a ``Point2`` that resolves to a
world-anchored ``Point2Value``, lives in :mod:`fungeom.primitives.point2.resolvers`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.frame2.value import WORLD_FRAME2, CoordinateFrame2
from fungeom.primitives.vec2.value import Float2, as_vec2


@dataclass(frozen=True, eq=False)
class Point2Value:
    """A 2D position expressed in ``frame`` — a framed planar vector.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for tolerant
    numeric comparison.
    """

    coord: Float2
    frame: CoordinateFrame2 = WORLD_FRAME2

    def __post_init__(self) -> None:
        coord = as_vec2(self.coord)
        freeze(coord)
        object.__setattr__(self, "coord", coord)

    @classmethod
    def of(cls, x: float, y: float, frame: CoordinateFrame2 = WORLD_FRAME2) -> Point2Value:
        """Build a point value from explicit coordinates in ``frame``."""
        return cls(coord=as_vec2((x, y)), frame=frame)

    @property
    def is_grounded(self) -> bool:
        """Whether this point's frame reaches :data:`WORLD_FRAME2`."""
        return self.frame.is_grounded

    def world(self) -> Point2Value:
        """This point re-expressed in :data:`WORLD_FRAME2`.

        Raises ``ValueError`` if the frame is not grounded — go through a ``Point2`` for a
        graceful answer.
        """
        if not self.frame.is_grounded:
            raise ValueError(f"frame {self.frame.name!r} is not grounded to the world")
        world_coord = self.frame.to_world().apply_point(self.coord)
        return Point2Value(coord=world_coord, frame=WORLD_FRAME2)

    def to_frame(self, frame: CoordinateFrame2) -> Point2Value:
        """This point re-expressed in ``frame`` (same physical location)."""
        if self.frame.root is not frame.root:
            raise ValueError(f"frames {self.frame.name!r} and {frame.name!r} are in different trees")
        new_coord = self.frame.transform_to(frame).apply_point(self.coord)
        return Point2Value(coord=new_coord, frame=frame)

    def approx_equal(self, other: Point2Value, atol: float = 1e-9) -> bool:
        """True if both points resolve to the same world position within ``atol``."""
        return bool(np.allclose(self.world().coord, other.world().coord, atol=atol))

    def __repr__(self) -> str:
        x, y = self.coord
        return f"Point2Value([{x:g}, {y:g}], frame={self.frame.name!r})"
