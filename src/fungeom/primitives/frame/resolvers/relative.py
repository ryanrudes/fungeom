"""The transform between two coordinate frames — partial when either is ungrounded."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class FrameTransform(Transform):
    """The rigid transform re-expressing ``frame``'s coordinates in ``other``.

    Resolvable iff both frames are grounded to the world — an ungrounded frame
    has no world-anchored placement, so the transform between them is undefined.
    """

    frame: Frame
    other: Frame

    def _decide(self) -> RigidTransformDecision:
        match self.frame.decide(), self.other.decide():
            case Resolvable(frame), Resolvable(other):
                return Resolvable(frame.transform_to(other))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
