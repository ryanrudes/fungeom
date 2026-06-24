"""Boundary policies — how a signal is read *outside* its sampled span.

A :class:`Boundary` is an enum-free *strategy object* (like
:class:`~fungeom.Interpolation`): a signal carries one to decide what an off-domain
query means. The default, :data:`Boundary.undefined`, refuses to invent data —
sampling outside the span is :class:`~fungeom.Unresolvable`. :data:`Boundary.hold`
clamps to the nearest end (the signal's first/last value persists outward).
:data:`Boundary.wrap` treats the signal as *periodic* — an off-domain time folds
back into the span modulo its length (for cyclic data, e.g. a gait phase).

A boundary maps an off-domain time onto an in-domain one (or to ``None`` when the
signal is genuinely undefined there); the signal then reconstructs at that time.
The boundary applies only past the *outer* edges of the support — never across an
interior gap, which stays ``Unresolvable``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar


class Boundary(ABC):
    """How to read a signal outside its sampled span."""

    undefined: ClassVar[Boundary]
    """Off-domain queries have no answer — sampling there is ``Unresolvable``."""

    hold: ClassVar[Boundary]
    """Clamp to the nearest end — the first/last sample persists outward."""

    wrap: ClassVar[Boundary]
    """Treat the signal as periodic — fold an off-domain time back into the span."""

    @abstractmethod
    def outside(self, t: float, domain: tuple[float, float]) -> float | None:
        """Map an off-domain ``t`` into ``domain``, or ``None`` if undefined there."""


@dataclass(frozen=True)
class _Undefined(Boundary):
    def outside(self, t: float, domain: tuple[float, float]) -> float | None:
        return None


@dataclass(frozen=True)
class _Hold(Boundary):
    def outside(self, t: float, domain: tuple[float, float]) -> float | None:
        low, high = domain
        return min(max(t, low), high)


@dataclass(frozen=True)
class _Wrap(Boundary):
    def outside(self, t: float, domain: tuple[float, float]) -> float | None:
        low, high = domain
        period = high - low
        if period == 0.0:  # a single-instant signal has nothing to wrap around
            return low
        return low + (t - low) % period


Boundary.undefined = _Undefined()
Boundary.hold = _Hold()
Boundary.wrap = _Wrap()
