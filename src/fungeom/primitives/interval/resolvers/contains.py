"""Membership of an instant in an interval — resolving to a ``Bool``.

Resolves into a :class:`~fungeom.Bool` but is built from an ``Interval`` and an
``Instant``, so it lives under ``interval`` (which already depends on both; the
reverse would be a cycle) — exactly as ``Vec3.norm`` lives under ``vec3`` and
resolves into a ``Scalar``.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval


@dataclass(frozen=True, eq=False)
class IntervalContains(Bool):
    """Whether ``instant`` lies within the closed span ``[start, end]`` of ``interval``."""

    interval: Interval
    instant: Instant

    def _decide(self) -> BoolDecision:
        match self.interval.decide(), self.instant.decide():
            case Resolvable(span), Resolvable(t):
                return Resolvable(span.start <= t <= span.end)
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
