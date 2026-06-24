"""A resolver for an already-known duration, plus float coercion."""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.core.resolvability import Resolvable
from fungeom.primitives.duration.decidability import DurationDecision
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.duration.value import as_duration


@dataclass(frozen=True, eq=False)
class LiteralDuration(Duration):
    """A duration that is already known — always resolvable.

    The field is named ``value`` (not ``seconds``) to avoid shadowing the
    :meth:`Duration.seconds` classmethod; it carries a plain ``float`` of seconds.
    """

    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", as_duration(self.value))

    def _decide(self) -> DurationDecision:
        return Resolvable(self.value)


def as_duration_resolver(value: float | Duration) -> Duration:
    """Lift a bare number of seconds into a literal resolver; pass durations through.

    This is the coercion that lets the fluent API accept plain floats while
    keeping every duration a graph node underneath.
    """
    if isinstance(value, Duration):
        return value
    return LiteralDuration(value=as_duration(value))
