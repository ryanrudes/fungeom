"""The ``Face`` interface — an oriented bounded patch (a plane carrying a 2D region).

The 3-D bounded surface a retarget *patch* is: a ``Plane`` (oriented surface) + a ``Region2``
(bounded area, in the plane's chart). The honest bounded-clearance object — :meth:`clearance`
clamps a query point *into* the region, so it is right even when the foot is beside, not above,
the patch (where the infinite-`Plane` distance would lie). Above ``plane`` / ``region2`` /
``point3`` in the layering; sibling concretes imported lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.face.value import FaceValue
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.coercion import SupportsPoint3, _as_point3
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.resolvers.base import Transform

if TYPE_CHECKING:
    from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
    from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle


class Face(Resolver[FaceValue]):
    """A deferred oriented bounded patch — a ``Plane`` plus a ``Region2`` in its 2-D chart.

    Construct with :meth:`on` (a plane + a region). Read it back with :meth:`plane` /
    :meth:`region`; query contact with :meth:`closest_point` (→ ``Point3``, clamped into the
    region) and :meth:`clearance` (→ ``Scalar``, the 3-D distance to the bounded patch).
    ``resolve()`` yields a ``FaceValue`` (``Face.Value``).

    Partial cases: an ungrounded plane or a degenerate region propagate; :meth:`closest_point`
    / :meth:`clearance` are ``Unresolvable`` when the region is empty (no surface points).
    """

    type Value = FaceValue
    """The resolved value type — a :class:`FaceValue` (plane + region)."""

    @classmethod
    def on(cls, plane: Plane, region: Region2) -> Face:
        """The bounded patch on ``plane`` cut out by ``region`` (in the plane's 2-D chart)."""
        from fungeom.primitives.face.resolvers.on import OnFace

        return OnFace(carrier=plane, outline=region)

    def plane(self) -> Plane:
        """The patch's oriented carrier plane (→ ``Plane``)."""
        from fungeom.primitives.face.resolvers.parts import FacePlane

        return FacePlane(face=self)

    def region(self) -> Region2:
        """The patch's bounded region, in the plane's 2-D chart (→ ``Region2``)."""
        from fungeom.primitives.face.resolvers.parts import FaceRegion

        return FaceRegion(face=self)

    def closest_point(self, point: Point3 | SupportsPoint3) -> Point3:
        """The point of the bounded patch nearest ``point`` (→ ``Point3``; clamped into the region).

        Unresolvable when the region is empty (the patch has no surface).
        """
        from fungeom.primitives.face.resolvers.closest_point import FaceClosestPoint

        return FaceClosestPoint(face=self, point=_as_point3(point))

    @overload
    def clearance(self, point: Point3 | SupportsPoint3) -> Scalar: ...
    @overload
    def clearance(self, point: Point3Bundle) -> ScalarBundle: ...
    def clearance(self, point: Point3 | SupportsPoint3 | Point3Bundle) -> Scalar | ScalarBundle:
        """The 3-D distance from ``point`` to the bounded patch (→ ``Scalar``; Unresolvable if empty).

        The *honest* footprint clearance: unlike ``Plane.distance_to`` (the infinite plane),
        this clamps into the region, so a foot beside the patch measures to its edge, not to the
        point directly below. Broadcasts over a ``Point3Bundle`` (→ ``ScalarBundle``, per marker).
        """
        from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle

        if isinstance(point, Point3Bundle):
            return point.map_scalar(lambda member: self.clearance(member))
        point = _as_point3(point)

        from fungeom.primitives.face.resolvers.clearance import FaceClearance

        return FaceClearance(face=self, point=point)

    def contains(self, point: Point3 | SupportsPoint3) -> Bool:
        """Whether ``point`` projects into this patch's footprint (→ ``Bool``).

        The support-polygon membership test — is the foot / CoM *over* the patch — independent of
        the normal-direction offset. Total (``False`` for an empty patch).
        """
        from fungeom.primitives.face.resolvers.contains import FaceContains

        return FaceContains(face=self, point=_as_point3(point))

    def transformed_by(self, transform: Transform) -> Face:
        """This patch moved rigidly in 3D (→ ``Face``; plane transported, footprint rotated with it).

        A rotation about the normal rotates the footprint (``R·v + t``); it is not merely re-centred
        — the region's chart coordinates are re-gauged to follow the moved chart.
        """
        from fungeom.primitives.face.resolvers.transformed import FaceTransformed

        return FaceTransformed(face=self, transform=transform)

    def frame(self) -> Transform:
        """The canonical patch frame (→ ``Transform``): origin at the region centroid, +z = the plane
        normal, +x = the plane's stable chart x-axis. Deterministic; Unresolvable for an empty face.
        """
        from fungeom.primitives.face.resolvers.frame import FaceFrame

        return FaceFrame(face=self)

    def boundary(self) -> Point3Bundle:
        """This patch's footprint vertices embedded in world, keyed ``0..N-1`` (→ ``Point3Bundle``)."""
        from fungeom.primitives.face.resolvers.boundary import FaceBoundary

        return FaceBoundary(face=self)
