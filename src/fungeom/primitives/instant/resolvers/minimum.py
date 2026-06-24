"""The earlier of two instants."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.instant.decidability import InstantDecision
from fungeom.primitives.instant.resolvers.base import Instant


@dataclass(frozen=True, eq=False)
class MinInstant(Instant):
    """``min(a, b)`` — the earlier instant; resolvable iff both are.

    Instants are master-clock seconds and so totally ordered, which is exactly
    what makes an earliest/latest meaningful (a ``Point3`` has no such order).
    """

    a: Instant
    b: Instant

    def _decide(self) -> InstantDecision:
        match self.a.decide(), self.b.decide():
            case Resolvable(a), Resolvable(b):
                return Resolvable(min(a, b))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
