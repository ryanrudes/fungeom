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

from collections.abc import Hashable

from scipy.spatial.transform import Rotation

from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.region2.value import Region2Value
from fungeom.primitives.transform.value import RigidTransform
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

    def transformed_by(self, transform: RigidTransform) -> FaceValue:
        """This patch moved rigidly in 3D — the plane is transported and the footprint rotates with it.

        The region lives in the plane's *normal-gauge* chart, whose basis is re-derived from the
        (transported) normal alone. A rotation about the normal leaves the normal — and so the
        chart — unchanged, so naively *keeping* the region's chart coordinates would drop that
        in-plane rotation and only move the centroid. We instead rotate the region by the gauge
        mismatch between the rotated old axes (``R·x``, ``R·y``) and the re-gauged new ones, so the
        footprint moves rigidly (``R·v + t``). A pure translation leaves the chart unchanged (the
        remap is the identity). The same fix the ``FaceSignal`` boundary/frame readbacks carry.
        """
        moved = self.plane.transformed_by(transform)
        x, y = self.plane.local_axes()
        new_x, new_y = moved.local_axes()
        rotation = transform.rotation
        rotated_x, rotated_y = rotation @ x, rotation @ y
        remap = np.array(
            [[rotated_x @ new_x, rotated_y @ new_x], [rotated_x @ new_y, rotated_y @ new_y]]
        )  # (u, v) ↦ (u', v'), a planar rotation in SO(2)
        return FaceValue(plane=moved, region=self.region.linearly_mapped(remap))

    def frame(self) -> RigidTransform:
        """The canonical patch frame: origin at the region centroid, +z = normal, +x = the plane's
        stable chart x-axis (raises if the region is empty / zero-area — no centroid)."""
        origin = self.plane.embed(self.region.centroid())  # centroid is in the chart; embed to 3D
        x, _y = self.plane.local_axes()
        z = self.plane.normal
        y = as_vec3(np.cross(z, x))
        rotation = Rotation.from_matrix(np.column_stack([x, y, z]))
        return RigidTransform.from_rotation(rotation, origin)

    def boundary_cloud(self) -> BundleValue[Point3Value]:
        """The footprint vertices embedded in 3D, keyed ``0..N-1`` in ring order (empty region → empty)."""
        coords = [vertex for ring in self.region.rings for vertex in ring]
        members: dict[Hashable, Point3Value] = {
            i: Point3Value(coord=self.plane.embed(coord), frame=WORLD_FRAME) for i, coord in enumerate(coords)
        }
        return BundleValue(roster=tuple(range(len(coords))), members=members)

    def __repr__(self) -> str:
        return f"FaceValue(plane={self.plane!r}, region={self.region!r})"
