"""A 2D frame placed relative to another (deferred) frame by a (deferred) transform."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame2.decidability import CoordinateFrame2Decision
from fungeom.primitives.frame2.resolvers.base import Frame2
from fungeom.primitives.transform2.resolvers.base import Transform2


@dataclass(frozen=True, eq=False)
class AttachedFrame2(Frame2):
    """A child frame positioned ``to_parent`` relative to ``parent`` — resolvable iff both are."""

    parent: Frame2
    name: str
    to_parent: Transform2

    def _decide(self) -> CoordinateFrame2Decision:
        match self.parent.decide(), self.to_parent.decide():
            case Resolvable(parent), Resolvable(to_parent):
                return Resolvable(parent.child(self.name, to_parent).world())
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
