"""A frame placed relative to another (deferred) frame by a (deferred) transform."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.frame.decidability import CoordinateFrameDecision
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.transform.resolvers.base import Transform


@dataclass(frozen=True, eq=False)
class AttachedFrame(Frame):
    """A child frame positioned ``to_parent`` relative to ``parent``.

    Both the parent frame *and* the placing transform are deferred, so this is
    resolvable iff both are; it resolves to the world-anchored child.
    """

    parent: Frame
    name: str
    to_parent: Transform

    def _decide(self) -> CoordinateFrameDecision:
        match self.parent.decide(), self.to_parent.decide():
            case Resolvable(parent), Resolvable(to_parent):
                return Resolvable(parent.child(self.name, to_parent).world())
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
