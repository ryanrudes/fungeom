"""The point3 *value*: a framed position.

A :class:`Point3Value` is a position together with the coordinate frame it is
expressed in — a *framed* vector, not a bare one. The deferred counterpart, a
``Point3`` that resolves to a world-anchored ``Point3Value``, lives in
:mod:`fungeom.primitives.point3.resolvers`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.frame import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class Point3Value:
    """A 3D position expressed in ``frame`` — a framed vector.

    Equality is identity-based (``eq=False``); use :meth:`approx_equal` for
    tolerant numeric comparison.
    """

    coord: Float3
    frame: CoordinateFrame = WORLD_FRAME

    def __post_init__(self) -> None:
        coord = as_vec3(self.coord)
        freeze(coord)
        object.__setattr__(self, "coord", coord)

    @classmethod
    def of(cls, x: float, y: float, z: float, frame: CoordinateFrame = WORLD_FRAME) -> Point3Value:
        """Build a point value from explicit coordinates in ``frame``."""
        return cls(coord=as_vec3((x, y, z)), frame=frame)

    @property
    def is_grounded(self) -> bool:
        """Whether this point's frame reaches :data:`WORLD_FRAME`."""
        return self.frame.is_grounded

    def world(self) -> Point3Value:
        """This point re-expressed in :data:`WORLD_FRAME`.

        Raises ``ValueError`` if the frame is not grounded — go through a
        ``Point3`` for a graceful answer.
        """
        if not self.frame.is_grounded:
            raise ValueError(f"frame {self.frame.name!r} is not grounded to the world")
        world_coord = self.frame.to_world().apply_point(self.coord)
        return Point3Value(coord=world_coord, frame=WORLD_FRAME)

    def to_frame(self, frame: CoordinateFrame) -> Point3Value:
        """This point re-expressed in ``frame`` (same physical location)."""
        if self.frame.root is not frame.root:
            raise ValueError(f"frames {self.frame.name!r} and {frame.name!r} are in different trees")
        new_coord = self.frame.transform_to(frame).apply_point(self.coord)
        return Point3Value(coord=new_coord, frame=frame)

    def approx_equal(self, other: Point3Value, atol: float = 1e-9) -> bool:
        """True if both points resolve to the same world position within ``atol``."""
        return bool(np.allclose(self.world().coord, other.world().coord, atol=atol))

    def __repr__(self) -> str:
        x, y, z = self.coord
        return f"Point3Value([{x:g}, {y:g}, {z:g}], frame={self.frame.name!r})"


def as_point3_block(coords: np.ndarray) -> tuple[Point3Value, ...]:
    """The rows of an ``(N, 3)`` array as **world-frame** point values — the bulk constructor.

    The vectorized counterpart of :meth:`Point3Value.of`, for the one shape that dominates a
    cloud: N positions already anchored in the world frame. It takes **one** copy and **one**
    :func:`~fungeom.core.arrays.freeze` for the whole block rather than one of each per row,
    which is what keeps a ``(T, N, 3)`` frame stack off the per-point coercion path — the
    per-row work is a view into the frozen block, not a fresh three-element array.

    The immutability guarantee is exactly :meth:`Point3Value.__post_init__`'s, taken once
    instead of row by row: the block is copied here, so a caller never aliases its own buffer
    into the values, and it is frozen before any view of it escapes, so no row can be written
    through. Raises ``ValueError`` if ``coords`` is not ``(N, 3)``.
    """
    block = np.array(coords, dtype=np.float64)  # copy; callers never alias into the values
    if block.ndim != 2 or block.shape[1] != 3:
        raise ValueError(f"Expected an (N, 3) block of 3D vectors, got shape {block.shape}.")
    freeze(block)
    points: list[Point3Value] = []
    for row in block:
        point = Point3Value.__new__(Point3Value)
        # The row is already canonical (float64, shape (3,)) and already read-only, so the
        # coercion __post_init__ would redo is skipped deliberately — the block paid for it.
        object.__setattr__(point, "coord", row)
        object.__setattr__(point, "frame", WORLD_FRAME)
        points.append(point)
    return tuple(points)
