"""A 2D point's coordinates in a given frame — the read-side inverse of ``Point2.in_frame``.

The 2D sibling of :class:`~fungeom.primitives.point3.resolvers.local_coordinates.LocalCoordinates3`:
a ``Vec2`` built from a point and a frame, living under ``point2`` to keep the dependency acyclic.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.vec2.decidability import Vec2Decision
from fungeom.primitives.vec2.resolvers.base import Vec2


@dataclass(frozen=True, eq=False)
class LocalCoordinates2(Vec2):
    """The coordinates of ``point`` re-expressed in ``frame`` — the inverse of ``Point2.in_frame``.

    Resolvable iff the point is and ``frame`` is grounded — a detached frame resolves to
    :class:`~fungeom.Unresolvable`, so it never reaches ``to_frame``.
    """

    point: Point2
    frame: Frame2

    def _decide(self) -> Vec2Decision:
        match self.point.decide(), self.frame.decide():
            case Resolvable(point), Resolvable(frame):
                return Resolvable(point.to_frame(frame).coord)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
