"""A time map recovered from a single landmark correspondence (offset only)."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable, Unresolvable
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.timemap.decidability import TimeMapDecision
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap


@dataclass(frozen=True, eq=False)
class AligningTimeMap(TimeMap):
    """The pure-offset map sending source-clock reading ``source`` to ``target``.

    A single correspondence fixes only the offset, not the rate, so the recovered
    map runs at unit rate (``offset = target − source``). This is the one-landmark
    sync — a known trigger or a hand-marked clap with no drift assumed. Total apart
    from propagation; recover drift as well with :meth:`TimeMap.through`.
    """

    source: Scalar
    target: Scalar

    def _decide(self) -> TimeMapDecision:
        match self.source.decide(), self.target.decide():
            case Resolvable(source), Resolvable(target):
                return Resolvable(AffineTimeMap(offset=target - source, rate=1.0))
            case Unresolvable() as bad, _:
                return bad
            case _, Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
