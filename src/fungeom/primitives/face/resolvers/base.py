"""The ``Face`` interface — an oriented bounded patch (a plane carrying a 2D region).

The 3-D bounded surface a retarget *patch* is: a ``Plane`` (oriented surface) + a ``Region2``
(bounded area, in the plane's chart). The honest bounded-clearance object — :meth:`clearance`
clamps a query point *into* the region, so it is right even when the foot is beside, not above,
the patch (where the infinite-`Plane` distance would lie). Above ``plane`` / ``region2`` /
``point3`` in the layering; sibling concretes imported lazily.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.face.value import FaceValue
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.scalar.resolvers.base import Scalar


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

    def closest_point(self, point: Point3) -> Point3:
        """The point of the bounded patch nearest ``point`` (→ ``Point3``; clamped into the region).

        Unresolvable when the region is empty (the patch has no surface).
        """
        from fungeom.primitives.face.resolvers.closest_point import FaceClosestPoint

        return FaceClosestPoint(face=self, point=point)

    def clearance(self, point: Point3) -> Scalar:
        """The 3-D distance from ``point`` to the bounded patch (→ ``Scalar``; Unresolvable if empty).

        The *honest* footprint clearance: unlike ``Plane.distance_to`` (the infinite plane),
        this clamps into the region, so a foot beside the patch measures to its edge, not to the
        point directly below.
        """
        from fungeom.primitives.face.resolvers.clearance import FaceClearance

        return FaceClearance(face=self, point=point)
