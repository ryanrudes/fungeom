"""A 3D point's coordinates in the plane's intrinsic 2D chart (→ Point2) — the 3D→2D bridge."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.value import WORLD_FRAME2
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point2.decidability import Point2Decision
from fungeom.primitives.point2.resolvers.base import Point2
from fungeom.primitives.point2.value import Point2Value
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class PlaneToLocal(Point2):
    """The chart coordinates of ``point`` on ``plane`` — orthogonally projected, in the plane's 2D gauge.

    The load-bearing 3D→2D link: it drops ``point``'s normal component and expresses the
    in-plane part in the plane's deterministic local basis (see :meth:`PlaneValue.local_axes`).
    Resolvable whenever the plane and point are (no extra partiality of its own).
    """

    plane: Plane
    point: Point3

    def _decide(self) -> Point2Decision:
        match self.plane.decide(), self.point.decide():
            case (Resolvable(plane), Resolvable(point)):
                return Resolvable(Point2Value(coord=plane.to_local(point.coord), frame=WORLD_FRAME2))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
