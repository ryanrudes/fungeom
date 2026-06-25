"""A face from a plane and a region (gathers the two)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.face.decidability import FaceDecision
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.face.value import FaceValue
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.region2.resolvers.base import Region2


@dataclass(frozen=True, eq=False)
class OnFace(Face):
    """The bounded patch on ``carrier`` cut out by ``outline`` — Unresolvable if either is.

    The fields are named ``carrier``/``outline`` (not ``plane``/``region``) so they don't shadow
    the :meth:`Face.plane` / :meth:`Face.region` accessor methods this concrete inherits.
    """

    carrier: Plane
    outline: Region2

    def _decide(self) -> FaceDecision:
        match self.carrier.decide(), self.outline.decide():
            case (Resolvable(plane), Resolvable(region)):
                return Resolvable(FaceValue(plane=plane, region=region))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
