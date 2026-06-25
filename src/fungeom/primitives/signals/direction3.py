"""``Direction3Signal`` — a unit direction that varies over time (a manifold signal).

A direction lives on a *sphere*, so its blend is **slerp** — genuinely *partial*:
there is no unique geodesic between antipodal directions, so ``between`` returns
:class:`~fungeom.Unresolvable` there. It plugs into the same generic core as the
flat signals, differing only in its blend; the manifold's partiality flows through
``at``/``resample`` like any other ``Unresolvable``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable, gather
from fungeom.primitives.direction3.decidability import Direction3Decision
from fungeom.primitives.direction3.resolvers.base import Direction3
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_lifted,
    decide_lifted_n,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    resolved_rows,
    decide_warped,
    support_from_times,
)
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp
from fungeom.primitives.vec3.value import as_vec3

if TYPE_CHECKING:
    from fungeom.primitives.signals.transform import TransformSignal

_PARALLEL = 1.0 - 1e-9


class _Direction3Blend:
    """Spherical-linear interpolation — partial between antipodal directions."""

    def between(self, a: Direction3Value, b: Direction3Value, frac: float) -> Resolvability[Direction3Value]:
        dot = float(np.clip(np.dot(a.vector, b.vector), -1.0, 1.0))
        if dot <= -_PARALLEL:
            return Unresolvable("no unique direction between antipodal directions")
        if dot >= _PARALLEL:
            return Resolvable(a)
        theta = float(np.arccos(dot))
        sin_theta = float(np.sin(theta))
        wa = float(np.sin((1.0 - frac) * theta)) / sin_theta
        wb = float(np.sin(frac * theta)) / sin_theta
        return Resolvable(Direction3Value(vector=as_vec3(wa * a.vector + wb * b.vector)))


DIRECTION3_BLEND = _Direction3Blend()


class Direction3Signal(Signal[Direction3Value]):
    """A deferred unit-direction-valued function of time, reconstructed by **slerp**.

    :meth:`at` / :meth:`resample` are additionally Unresolvable wherever the
    interpolation would cross antipodal samples. :meth:`at` returns a rich
    ``Direction3``; ``resolve()`` yields a ``SampledSeries[Direction3Value]``.
    """

    type Value = SampledSeries[Direction3Value]
    """The resolved value type — a ``SampledSeries`` of unit directions."""

    @classmethod
    def sampled(
        cls,
        sampling: Sampling,
        values: Sequence[Sequence[float]],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> Direction3Signal:
        """A signal of direction ``values`` (each normalized) over ``sampling``.

        Samples spaced more than ``max_gap`` seconds apart are treated as a dropout.
        """
        return _SampledDirection3Signal(
            sampling=sampling,
            directions=tuple(Direction3.of(*(float(c) for c in row)) for row in values),
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    @classmethod
    def from_samples(
        cls,
        times: ArrayLike,
        values: Sequence[Sequence[float]],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> Direction3Signal:
        """A signal sampled at explicit ``times`` (sugar over :meth:`sampled`)."""
        return cls.sampled(Sampling.at_times(times), values, via=via, outside=outside, max_gap=max_gap)

    def at(self, instant: Instant | float) -> Direction3:
        """The direction at ``instant`` (Unresolvable off-domain or across antipodes)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _Direction3SampleAt(signal=self, instant=as_instant_resolver(instant))

    def resample(self, onto: Sampling) -> Direction3Signal:
        """This signal reconstructed onto a new time base."""
        return _ResampledDirection3Signal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> Direction3Signal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedDirection3Signal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedDirection3Signal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> Direction3Signal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedDirection3Signal(source=self, to=window)

    def shift(self, by: Duration | float) -> Direction3Signal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        """Resample onto ``onto`` and resolve to a raw ``(T, 3) array`` — the vectorized readback.

        The sanctioned exit into numpy; resolves eagerly (raises ``UnresolvableError`` if a
        target is off the support).
        """
        return resolved_rows(self.resample(onto), lambda value: value.vector)

    @classmethod
    def lift(cls, sources: Sequence[Signal[Any]], combine: Callable[..., Direction3]) -> Direction3Signal:
        """Build a direction signal by combining ``sources`` per instant (the general escape hatch)."""
        return _LiftedDirection3Signal(sources=tuple(sources), combine=combine)

    def map(self, transform: Callable[[Direction3], Direction3]) -> Direction3Signal:
        """Apply ``transform`` to this direction at each instant (→ ``Direction3Signal``; the unary lift)."""
        return _LiftedDirection3Signal(sources=(self,), combine=transform)

    def rotated_by(self, pose: TransformSignal) -> Direction3Signal:
        """This direction rotated by a moving ``pose`` over time (→ ``Direction3Signal``).

        The transport lift for a direction — the pose's rotation is applied (translation is
        meaningless for a direction); time-aligned ∩ supports, off the pose's support →
        ``Unresolvable``.
        """
        return _RotatedDirection3Signal(a=self, pose=pose)


@dataclass(frozen=True, eq=False)
class _RotatedDirection3Signal(Direction3Signal):
    """A direction rotated by a moving pose over time — the transport lift."""

    a: Direction3Signal
    pose: TransformSignal

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        return decide_lifted(
            self.a, self.pose, lambda t: self.pose.at(t).transform_direction(self.a.at(t)), DIRECTION3_BLEND
        )


@dataclass(frozen=True, eq=False)
class _LiftedDirection3Signal(Direction3Signal):
    """A direction signal built by combining N sources per instant — the general lift / map."""

    sources: tuple[Signal[Any], ...]
    combine: Callable[..., Direction3]

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        return decide_lifted_n(self.sources, lambda t: self.combine(*(s.at(t) for s in self.sources)), DIRECTION3_BLEND)


@dataclass(frozen=True, eq=False)
class _SampledDirection3Signal(Direction3Signal):
    """Normalizes each sample through the ``Direction3`` resolver before building the series.

    Like ``_SampledPoint3Signal``, this routes samples through their primitive so a
    value-dependent partiality — here a *zero-vector* sample, which has no direction —
    surfaces as ``Unresolvable`` rather than raising at construction.
    """

    sampling: Sampling
    directions: tuple[Direction3, ...]
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        match self.sampling.decide():
            case Resolvable(base):
                if len(self.directions) != base.count:
                    return Unresolvable(f"{len(self.directions)} values for {base.count} sample times")
                decided = gather(direction.decide() for direction in self.directions)
                if isinstance(decided, Unresolvable):
                    return decided
                return Resolvable(
                    SampledSeries(
                        base.times,
                        tuple(decided.value),
                        self.interpolation,
                        self.boundary,
                        DIRECTION3_BLEND,
                        support_from_times(base.times, self.max_gap),
                    )
                )
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _ResampledDirection3Signal(Direction3Signal):
    source: Direction3Signal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedDirection3Signal(Direction3Signal):
    source: Direction3Signal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedDirection3Signal(Direction3Signal):
    source: Direction3Signal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _Direction3SampleAt(Direction3):
    signal: Direction3Signal
    instant: Instant

    def _decide(self) -> Direction3Decision:
        return decide_sample(self.signal, self.instant)
