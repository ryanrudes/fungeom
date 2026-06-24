"""The 2D transform between two coordinate frames — partial when either is ungrounded."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.transform2.decidability import RigidTransform2Decision
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class Frame2Transform(Transform2):
    """The rigid 2D transform re-expressing ``frame``'s coordinates in ``other``.

    Resolvable iff both frames are grounded to the world.
    """

    frame: Frame2
    other: Frame2

    def _decide(self) -> RigidTransform2Decision:
        match self.frame.decide(), self.other.decide():
            case Resolvable(frame), Resolvable(other):
                return Resolvable(frame.transform_to(other))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
