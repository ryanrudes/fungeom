"""The face *value*: an oriented bounded patch — a plane carrying a 2D region.

A :class:`FaceValue` (``Face``/``OrientedRegion3``) is the 3-D bounded surface a retarget
*patch* is: a :class:`~fungeom.values.PlaneValue` (the oriented surface) plus a
:class:`~fungeom.values.Region2Value` (the bounded area, in the plane's intrinsic 2-D chart).
It is the honest *bounded* contact surface — its clearance clamps a query point into the
region (like ``Segment.project`` vs ``Line.project``), so the distance is right even when the
foot is *beside*, not above, the patch.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.region2.value import Region2Value
from fungeom.primitives.vec3.value import Float3, as_vec3


@dataclass(frozen=True, eq=False)
class FaceValue:
    """An oriented bounded patch: a ``plane`` plus a ``region`` in its 2-D chart.

    Equality is identity-based (``eq=False``). A face with an empty region has no surface
    points, so :meth:`closest_point` / :meth:`clearance` raise — go through a ``Face`` resolver
    for a graceful ``Unresolvable``.
    """

    plane: PlaneValue
    region: Region2Value

    def closest_point(self, p: Float3) -> Float3:
        """The point of the bounded patch nearest ``p`` — clamped into the region (raises if empty).

        Project ``p`` into the plane's chart; if that lands inside the region it *is* the
        closest point (directly below ``p``), otherwise clamp to the region's nearest boundary
        point. Either way, embed back to 3-D world.
        """
        local = self.plane.to_local(as_vec3(p))
        clamped = local if self.region.contains(local) else self.region.nearest_boundary_point(local)
        return self.plane.embed(clamped)

    def clearance(self, p: Float3) -> float:
        """The 3-D distance from ``p`` to the nearest point of the bounded patch (raises if empty)."""
        return float(np.linalg.norm(as_vec3(p) - self.closest_point(p)))

    def contains(self, p: Float3) -> bool:
        """Whether ``p`` projects into the patch footprint — the region contains its in-plane projection.

        The support-polygon membership test (is the foot / CoM *over* the patch), independent of the
        normal-direction offset. ``False`` for an empty region (no footprint)."""
        return self.region.contains(self.plane.to_local(as_vec3(p)))

    def __repr__(self) -> str:
        return f"FaceValue(plane={self.plane!r}, region={self.region!r})"
