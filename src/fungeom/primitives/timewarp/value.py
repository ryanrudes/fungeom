"""The time-warp *value*: a monotonic, piecewise-linear reparametrization of time.

A :class:`PiecewiseLinearWarp` is the content-warping counterpart of the affine
:class:`~fungeom.primitives.timemap.value.AffineTimeMap`: where a time map relates
two *clocks* by a single offset and rate, a warp bends a signal's *own* time axis
through a sequence of correspondence knots. It is order-preserving by construction
(strictly increasing in both source and target), so it is defined only over the
closed span of its source knots and is always invertible (swap the two knot lists).
The strict-monotonicity invariant is enforced upstream by the
:class:`~fungeom.primitives.timewarp.resolvers.base.TimeWarp` resolver, which
returns :class:`~fungeom.Unresolvable` for non-monotonic knots rather than building
an invalid value.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class PiecewiseLinearWarp:
    """A monotonic piecewise-linear map ``source[i] ↦ target[i]`` (linear between knots)."""

    source: tuple[float, ...]
    target: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", tuple(float(x) for x in self.source))
        object.__setattr__(self, "target", tuple(float(x) for x in self.target))

    @property
    def domain(self) -> tuple[float, float]:
        """The closed span of source times the warp is defined over."""
        return (self.source[0], self.source[-1])

    def apply(self, t: float) -> float:
        """Map a source time ``t`` (within :attr:`domain`) through the warp."""
        knots = self.source
        if t <= knots[0]:
            return self.target[0]
        if t >= knots[-1]:
            return self.target[-1]
        i = bisect.bisect_right(knots, t)
        s0, s1 = knots[i - 1], knots[i]
        u0, u1 = self.target[i - 1], self.target[i]
        return u0 + (u1 - u0) * (t - s0) / (s1 - s0)

    def inverse(self) -> PiecewiseLinearWarp:
        """The inverse warp (target → source) — total, since the warp is strictly monotonic."""
        return PiecewiseLinearWarp(source=self.target, target=self.source)

    def __repr__(self) -> str:
        return f"PiecewiseLinearWarp({len(self.source)} knots over {self.domain})"
