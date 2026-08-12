"""The ``Sampling`` interface — building a discrete time base.

A sampling is the time axis of discrete data: a strictly-increasing set of
instants. Build one from explicit timestamps (real, jittery data), as a uniform
grid over an interval, or from a rate and a sample count. Sibling resolver types
are imported lazily to keep module load acyclic; the lower-layer ``Interval`` and
``Instant`` are imported normally.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.core.arrays import ArrayLike
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.sampling.value import SamplingValue
from fungeom.primitives.scalar.resolvers.base import Scalar


class Sampling(Resolver[SamplingValue]):
    """A deferred discrete time base — a strictly-increasing set of instants.

    Construct one with :meth:`at_times` (explicit timestamps, e.g. straight from a
    capture), :meth:`uniform` (an evenly-spaced grid over an interval), or
    :meth:`at_rate` (that same grid from a rate and a sample count); query it
    with :meth:`span` (→ ``Interval``), :meth:`count` (→ ``Scalar``), and
    :meth:`rate` (→ ``Scalar``, the mean Hz). ``resolve()`` yields a
    :class:`~fungeom.primitives.sampling.value.SamplingValue` (``Sampling.Value``).

    Every constructor is *partial*: a sampling with no times, or with duplicate or
    out-of-order timestamps, is :class:`~fungeom.Unresolvable` — a corrupt time
    base defines no function of time, and the library refuses to pretend otherwise.
    """

    type Value = SamplingValue
    """The resolved value type — a :class:`SamplingValue`."""

    @classmethod
    def at_times(cls, times: ArrayLike) -> Sampling:
        """A sampling at the given explicit timestamps (must be strictly increasing)."""
        from fungeom.primitives.sampling.resolvers.explicit import ExplicitSampling
        from fungeom.primitives.sampling.value import as_times

        return ExplicitSampling(times=tuple(as_times(times).tolist()))

    @classmethod
    def uniform(cls, over: Interval, count: int) -> Sampling:
        """A grid of ``count`` evenly-spaced instants spanning ``over``."""
        from fungeom.primitives.sampling.resolvers.uniform import UniformSampling

        return UniformSampling(over=over, samples=count)

    @classmethod
    def at_rate(cls, rate: float | Scalar, count: int, start: Instant | float = 0.0) -> Sampling:
        """``count`` instants at ``rate`` Hz, the first at ``start`` (the epoch by default).

        The same grid as :meth:`uniform`, parameterized the way discrete data arrives:
        recordings know how fast they were sampled and how many samples they hold, not the
        span those samples cover. Deriving that span means writing ``count - 1`` — one
        fewer interval than there are samples — at every call site, which is an off-by-one
        waiting to happen; this puts it in one place.

        Partial for fewer than one sample, for a rate that is not positive (zero, negative
        or NaN), and for a rate so large that the spacing underflows to nothing.
        """
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver
        from fungeom.primitives.sampling.resolvers.paced import PacedSampling
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver

        return PacedSampling(
            start_at=as_instant_resolver(start),
            rate_hz=as_scalar_resolver(rate),
            samples=count,
        )

    def span(self) -> Interval:
        """The closed interval ``[first, last]`` this sampling covers."""
        from fungeom.primitives.sampling.resolvers.span import SamplingSpan

        return SamplingSpan(sampling=self)

    def count(self) -> Scalar:
        """The number of samples, as a deferred scalar."""
        from fungeom.primitives.sampling.resolvers.count import SamplingCount

        return SamplingCount(sampling=self)

    def rate(self) -> Scalar:
        """The mean sample rate in Hz (Unresolvable with fewer than two samples)."""
        from fungeom.primitives.sampling.resolvers.rate import SamplingRate

        return SamplingRate(sampling=self)
