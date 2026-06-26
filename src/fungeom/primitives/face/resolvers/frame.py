"""The canonical patch frame of a Face (→ Transform)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class FaceFrame(Transform):
    """The patch frame of ``face`` — origin at the region centroid, +z = the plane normal, +x = the
    plane's stable chart x-axis. Deterministic (same face → same frame). Unresolvable for an empty
    face (no centroid).
    """

    face: Face

    def _decide(self) -> RigidTransformDecision:
        match self.face.decide():
            case Resolvable(face):
                if face.region.is_empty:
                    return Unresolvable("an empty face has no frame")
                return Resolvable(face.frame())
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
