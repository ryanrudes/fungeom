"""Numeric surface fits over a point cloud (PCA / SVD).

fungeom *calls* numerics, it does not *own* them: the SVD lives here, behind a
resolver whose only job is to surface numerical degeneracy as ``Unresolvable``. The
decidability is tolerance-based (a fit over real data is never *exactly* degenerate) —
the honest model for a fit, distinct from the exact-zero checks of the algebraic
constructors (e.g. ``Plane.through_points``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.line.decidability import LineDecision
from fungeom.primitives.line.resolvers.base import Line
from fungeom.primitives.line.value import LineValue
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.plane.value import PlaneValue


def orient_plane_track(planes: list[PlaneValue]) -> list[PlaneValue]:
    """Flip each plane's normal to agree with the previous one — a continuous normal track.

    The per-frame SVD normal sign is arbitrary, so a fitted *moving* plane can flip sign between
    frames and read as antipodal (breaking the slerp blend). This walks the track and negates any
    normal opposed to its predecessor, so consecutive normals vary smoothly.
    """
    oriented: list[PlaneValue] = []
    previous: np.ndarray | None = None
    for plane in planes:
        if previous is not None and float(np.dot(plane.normal, previous)) < 0.0:
            plane = plane.flipped()
        previous = plane.normal
        oriented.append(plane)
    return oriented


def fit_plane_coords(points: np.ndarray, tolerance: float) -> Resolvability[PlaneValue]:
    """The least-squares plane through ``points`` (an ``(N, 3)`` array) — the shared SVD kernel.

    Unresolvable with fewer than three points, or when the normal direction is not unique (the
    gap between the two smallest singular values is within ``tolerance`` of the cloud's scale).
    The normal's sign is the SVD convention (arbitrary). Used both by :class:`FittedPlane` and,
    per frame, by ``Point3BundleSignal.fit_plane``.
    """
    if points.shape[0] < 3:
        return Unresolvable("a plane fit needs at least three present points")
    centroid = points.mean(axis=0)
    _, singular, right = np.linalg.svd(points - centroid, full_matrices=False)
    if singular[1] - singular[2] <= tolerance * singular[0]:
        return Unresolvable("the points have no unique normal direction (near-collinear or isotropic)")
    return Resolvable(PlaneValue(point=centroid, normal=right[2]))


@dataclass(frozen=True, eq=False)
class FittedPlane(Plane):
    """The least-squares plane through ``cloud``'s present points (principal-component fit).

    The normal is the least-variance (smallest-singular-value) direction of the centered
    points. **Unresolvable** when there are fewer than three present points, or when that
    direction is not unique — the gap between the two smallest singular values is within
    ``tolerance`` of the cloud's scale (the largest singular value). That single gap test
    captures *both* near-collinear (rod-like) and near-isotropic (ball-like) clouds, the
    two ways a normal can be ambiguous. The normal's sign is arbitrary (SVD convention) —
    resolve it downstream with :meth:`Plane.facing`.
    """

    cloud: Point3Bundle
    tolerance: float

    def _decide(self) -> PlaneDecision:
        match self.cloud.decide():
            case Resolvable(collection):
                points = np.array([collection.members[key].coord for key in collection.support()])
                return fit_plane_coords(points, self.tolerance)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class FittedLine(Line):
    """The least-squares line through ``cloud``'s present points (principal-component fit).

    The direction is the most-variance (largest-singular-value) direction of the centered
    points. **Unresolvable** when there are fewer than two present points, or when that
    direction is not dominant — the gap between the two largest singular values is within
    ``tolerance`` of the cloud's scale (the largest singular value). That gap test catches
    an isotropic cloud with no principal axis (e.g. a symmetric ring or ball). The
    direction's sign is arbitrary (SVD convention) — orient it with
    :meth:`Line.direction_along`.
    """

    cloud: Point3Bundle
    tolerance: float

    def _decide(self) -> LineDecision:
        match self.cloud.decide():
            case Resolvable(collection):
                points = np.array([collection.members[key].coord for key in collection.support()])
                if points.shape[0] < 2:
                    return Unresolvable("a line fit needs at least two present points")
                centroid = points.mean(axis=0)
                _, singular, right = np.linalg.svd(points - centroid, full_matrices=False)
                if singular[0] - singular[1] <= self.tolerance * singular[0]:
                    return Unresolvable("the points have no dominant direction (isotropic)")
                return Resolvable(LineValue(point=centroid, direction=right[0]))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
