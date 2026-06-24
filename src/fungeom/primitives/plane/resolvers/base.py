"""The ``Plane`` interface — an oriented plane and its surface algebra.

A plane is the natural home for surface geometry: project a point onto it, measure
signed distance, orient its normal toward a reference, shift it along the normal, and
build a local coordinate frame on it. Constructors fix the plane from a point + normal,
three points, or two spanning vectors; the combinators return the matching primitive
(``Point3`` / ``Scalar`` / ``Bool`` / ``Direction3`` / ``Plane`` / ``Transform``).
Sibling concrete resolvers are imported lazily to keep module load acyclic; the
lower-layer primitives are imported normally.
"""

from __future__ import annotations

from collections.abc import Sequence

from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.vec3.resolvers.base import Vec3


class Plane(Resolver[PlaneValue]):
    """A deferred oriented plane — a point on it and a (meaningful) outward normal.

    Construct with :meth:`through` (point + normal), :meth:`through_points` (three
    points), or :meth:`spanned_by` (point + two in-plane vectors). Read it with
    :meth:`normal` / :meth:`origin`, :meth:`project`, :meth:`signed_distance`,
    :meth:`distance_to`, :meth:`contains`; reshape it with :meth:`facing` (orient the
    normal toward a point), :meth:`flipped`, :meth:`offset` (a parallel shift); project a
    direction into it with :meth:`project_direction`; and build a surface coordinate
    frame with :meth:`frame`. ``resolve()`` yields a ``PlaneValue`` (``Plane.Value``).

    Partial cases: :meth:`through_points`/:meth:`spanned_by` are ``Unresolvable`` for
    collinear/parallel inputs; :meth:`facing` for a point *on* the plane;
    :meth:`project_direction` and :meth:`frame` for a direction parallel to the normal.
    """

    type Value = PlaneValue
    """The resolved value type — an oriented :class:`PlaneValue`."""

    @classmethod
    def through(cls, point: Point3, normal: Direction3) -> Plane:
        """The plane through ``point`` with the given ``normal``."""
        from fungeom.primitives.plane.resolvers.through import PlaneThrough

        return PlaneThrough(anchor=point, axis=normal)

    @classmethod
    def through_points(cls, a: Point3, b: Point3, c: Point3) -> Plane:
        """The plane through three points (Unresolvable if they are collinear).

        The normal follows the right-hand rule on ``(b - a) × (c - a)``.
        """
        from fungeom.primitives.plane.resolvers.through_points import PlaneThroughPoints

        return PlaneThroughPoints(a=a, b=b, c=c)

    @classmethod
    def spanned_by(cls, point: Point3, u: Vec3, v: Vec3) -> Plane:
        """The plane through ``point`` spanned by ``u`` and ``v`` (Unresolvable if parallel)."""
        from fungeom.primitives.plane.resolvers.spanned_by import PlaneSpannedBy

        return PlaneSpannedBy(anchor=point, u=u, v=v)

    def normal(self) -> Direction3:
        """This plane's unit outward normal (→ ``Direction3``)."""
        from fungeom.primitives.plane.resolvers.normal import PlaneNormal

        return PlaneNormal(plane=self)

    def origin(self) -> Point3:
        """The plane's representative point (→ ``Point3``)."""
        from fungeom.primitives.plane.resolvers.origin import PlaneOrigin

        return PlaneOrigin(plane=self)

    def project(self, point: Point3) -> Point3:
        """The orthogonal projection of ``point`` onto this plane (→ ``Point3``)."""
        from fungeom.primitives.plane.resolvers.project import PlaneProject

        return PlaneProject(plane=self, point=point)

    def signed_distance(self, point: Point3) -> Scalar:
        """The signed distance from ``point`` to the plane (positive on the normal side)."""
        from fungeom.primitives.plane.resolvers.signed_distance import PlaneSignedDistance

        return PlaneSignedDistance(plane=self, point=point)

    def distance_to(self, point: Point3) -> Scalar:
        """The unsigned distance from ``point`` to the plane (``|signed_distance|``)."""
        return abs(self.signed_distance(point))

    def contains(self, point: Point3, tolerance: float = 1e-9) -> Bool:
        """Whether ``point`` lies on the plane within ``tolerance`` (→ ``Bool``)."""
        return abs(self.signed_distance(point)).le(tolerance)

    def facing(self, point: Point3) -> Plane:
        """This plane with its normal oriented toward ``point`` (Unresolvable if on the plane)."""
        from fungeom.primitives.plane.resolvers.facing import PlaneFacing

        return PlaneFacing(plane=self, point=point)

    def flipped(self) -> Plane:
        """This plane with the opposite normal."""
        from fungeom.primitives.plane.resolvers.flipped import PlaneFlipped

        return PlaneFlipped(plane=self)

    def offset(self, distance: Scalar | float) -> Plane:
        """A parallel plane shifted ``distance`` along the normal (a contact-surface offset)."""
        from fungeom.primitives.plane.resolvers.offset import PlaneOffset
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return PlaneOffset(plane=self, distance=as_scalar_resolver(distance))

    def project_direction(self, direction: Direction3) -> Direction3:
        """``direction`` projected into the plane and renormalized (Unresolvable if normal-parallel)."""
        from fungeom.primitives.plane.resolvers.project_direction import PlaneProjectDirection

        return PlaneProjectDirection(plane=self, direction=direction)

    def frame(self, origin: Point3, tangent: Direction3) -> Transform:
        """A surface coordinate frame at ``origin`` (→ ``Transform``): ``z`` = normal, ``x`` = in-plane ``tangent``.

        The canonical right-handed frame placing the patch in the world: the plane's
        normal is the local ``+z``, ``tangent`` projected into the plane is ``+x``, and
        ``+y = z × x``. Unresolvable when ``tangent`` is parallel to the normal (no
        in-plane component). Handedness / axis conventions other than this canonical one
        are a caller concern (compose a fixed convention transform).
        """
        from fungeom.primitives.plane.resolvers.frame import PlaneFrame

        return PlaneFrame(plane=self, origin=origin, tangent=tangent)

    def winding_normal(self, points: Sequence[Point3], tolerance: float = 1e-9) -> Direction3:
        """The normal whose side ``points`` wind counter-clockwise around (→ ``Direction3``).

        The points are projected onto the plane and read as an ordered polygon; the
        signed area vector (``½ Σ (pᵢ − c) × (pᵢ₊₁ − c)``, cyclic, about their centroid
        ``c``) points to the side from which the winding looks counter-clockwise — by the
        right-hand rule, ``±`` this plane's own normal. This resolves a winding-based
        normal orientation. Unresolvable with fewer than three points, or when the
        enclosed area is within ``tolerance`` of the cloud's scale (collinear / zero-area).
        """
        from fungeom.primitives.plane.resolvers.winding_normal import PlaneWindingNormal

        return PlaneWindingNormal(plane=self, points=tuple(points), tolerance=tolerance)
