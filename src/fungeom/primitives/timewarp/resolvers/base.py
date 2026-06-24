"""The ``TimeWarp`` interface — the monotonic content-warp algebra.

A time warp is the content-warping counterpart of the affine :class:`~fungeom.TimeMap`:
where a time map relates two *clocks* (offset + rate), a warp bends a signal's *own*
time axis through a sequence of correspondence knots. It is the type that
reparametrizes a :class:`~fungeom.primitives.signals.series.Signal` non-affinely —
drift correction from many sync points, easing, a hand-authored stretch. The knots
are plain numbers (a warp is a reconstruction *strategy*, like
:class:`~fungeom.primitives.signals.interpolation.Interpolation`, not a deferred
graph of scalars); the lower-layer value type is imported normally and the sibling
concrete resolvers lazily, to keep module load acyclic.

What *discovers* the knots from raw signals (cross-correlation, dynamic time
warping) is deliberately out of scope — that is a numerics kernel that *produces* a
``TimeWarp``; this facade is the exact, decidable warp you build from known
correspondences.
"""

from __future__ import annotations

from collections.abc import Sequence

from fungeom.core.resolver import Resolver
from fungeom.primitives.timewarp.value import PiecewiseLinearWarp


class TimeWarp(Resolver[PiecewiseLinearWarp]):
    """A deferred monotonic, piecewise-linear reparametrization of a signal's time.

    Construct one with :meth:`through` (a sequence of ``(source, target)`` knots);
    invert with :meth:`inverse`. ``resolve()`` yields a
    :class:`~fungeom.primitives.timewarp.value.PiecewiseLinearWarp` (``TimeWarp.Value``),
    which a signal's :meth:`reparameterize` reads to bend its time base.

    The one *partial* construction is :meth:`through`: a warp must preserve order, so
    knots whose source *or* target readings are not strictly increasing (or fewer
    than two of them) are :class:`~fungeom.Unresolvable`. :meth:`inverse` is total
    apart from propagation, since a strictly-monotonic warp is always invertible.
    """

    type Value = PiecewiseLinearWarp
    """The resolved value type — a :class:`PiecewiseLinearWarp`."""

    @classmethod
    def through(cls, knots: Sequence[tuple[float, float]]) -> TimeWarp:
        """The monotonic warp through the given ``(source, target)`` correspondence knots.

        Reconstruction is linear between knots. Unresolvable if there are fewer than
        two knots, or if either the source or the target readings are not strictly
        increasing (a warp must preserve order) — this is the N-landmark
        generalization of :meth:`TimeMap.through`, exact rather than a fitted line.
        """
        from fungeom.primitives.timewarp.resolvers.through import ThroughTimeWarp

        return ThroughTimeWarp(
            sources=tuple(float(s) for s, _ in knots),
            targets=tuple(float(t) for _, t in knots),
        )

    def inverse(self) -> TimeWarp:
        """The inverse warp (target → source), swapping the correspondence knots."""
        from fungeom.primitives.timewarp.resolvers.inverse import InverseTimeWarp

        return InverseTimeWarp(warp=self)
