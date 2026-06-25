"""Accessors for a face's constituent plane and region."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2


@dataclass(frozen=True, eq=False)
class FacePlane(Plane):
    """The carrier plane of ``face`` (→ ``Plane``)."""

    face: Face

    def _decide(self) -> PlaneDecision:
        match self.face.decide():
            case Resolvable(face):
                return Resolvable(face.plane)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class FaceRegion(Region2):
    """The bounded region of ``face``, in the plane's 2-D chart (→ ``Region2``)."""

    face: Face

    def _decide(self) -> Region2Decision:
        match self.face.decide():
            case Resolvable(face):
                return Resolvable(face.region)
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
