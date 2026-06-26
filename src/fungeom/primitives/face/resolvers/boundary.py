"""A Face's footprint vertices embedded in 3D (→ Point3Bundle)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class FaceBoundary(Point3Bundle):
    """The boundary vertices of ``face`` embedded in world, keyed ``0..N-1`` in ring order — total
    (an empty face yields an empty cloud).
    """

    face: Face

    def _decide(self) -> BundleDecision[Point3Value]:
        match self.face.decide():
            case Resolvable(face):
                return Resolvable(face.boundary_cloud())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
