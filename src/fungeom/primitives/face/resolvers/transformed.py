"""A bounded patch moved rigidly in 3D."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.face.decidability import FaceDecision
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class FaceTransformed(Face):
    """``face`` moved by a rigid ``transform`` — the plane is transported and the footprint rotates
    with it (``R·v + t``), not merely re-centred. Total: partiality only propagates from the inputs.
    """

    face: Face
    transform: Transform

    def _decide(self) -> FaceDecision:
        match self.face.decide(), self.transform.decide():
            case (Resolvable(face), Resolvable(transform)):
                return Resolvable(face.transformed_by(transform))
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
