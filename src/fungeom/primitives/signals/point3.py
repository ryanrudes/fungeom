"""``Point3Signal`` — a framed position that varies over time.

The trajectory of a point — and the case that exercises a *second* partiality axis
the other signals don't have: **frame grounding**. A point's samples live in some
coordinate frame, and a point in a detached frame cannot be world-anchored. So,
unlike the flat/manifold signals, the samples are kept as deferred ``Point3``
*resolvers* and grounded at *build* time (a point on an ungrounded frame makes the
whole signal :class:`~fungeom.Unresolvable`). Once grounded, the blend is a plain
world-space lerp, and the rest of the generic core is reused unchanged — the one
place this type needs its own ``decide`` is the grounding pass.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable, gather
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.scalar import SCALAR_BLEND, ScalarSignal
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_lifted,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    support_from_times,
)
from fungeom.primitives.signals.vec3 import VEC3_BLEND, Vec3Signal
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.vec3.value import Float3, as_vec3


class _Point3Blend:
    """World-space linear interpolation of (already-grounded) points — total."""

    def between(self, a: Point3Value, b: Point3Value, frac: float) -> Resolvability[Point3Value]:
        coord = as_vec3(a.coord + frac * (b.coord - a.coord))
        return Resolvable(Point3Value(coord=coord, frame=WORLD_FRAME))


POINT3_BLEND = _Point3Blend()


class Point3Signal(Signal[Point3Value]):
    """A deferred position-valued function of time.

    Samples are positions in a coordinate ``frame``; resolving world-anchors them,
    so an ungrounded frame makes the signal Unresolvable (the second partiality
    axis). :meth:`at` returns a rich ``Point3``; ``resolve()`` yields a
    ``SampledSeries[Point3Value]``.
    """

    type Value = SampledSeries[Point3Value]
    """The resolved value type — a ``SampledSeries`` of world-anchored positions."""

    @classmethod
    def sampled(
        cls,
        sampling: Sampling,
        values: Sequence[Sequence[float]],
        frame: CoordinateFrame = WORLD_FRAME,
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> Point3Signal:
        """A signal of ``(N, 3)`` positions in ``frame`` over ``sampling``.

        Samples spaced more than ``max_gap`` seconds apart are treated as a dropout.
        """
        points = tuple(Point3.at(x, y, z, frame=frame) for x, y, z in values)
        return _SampledPoint3Signal(
            sampling=sampling,
            points=points,
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    @classmethod
    def from_samples(
        cls,
        times: ArrayLike,
        values: Sequence[Sequence[float]],
        frame: CoordinateFrame = WORLD_FRAME,
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> Point3Signal:
        """A signal sampled at explicit ``times`` (sugar over :meth:`sampled`)."""
        return cls.sampled(Sampling.at_times(times), values, frame=frame, via=via, outside=outside, max_gap=max_gap)

    def at(self, instant: Instant | float) -> Point3:
        """The position at ``instant`` (Unresolvable off-domain or on an ungrounded frame)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _Point3SampleAt(signal=self, instant=as_instant_resolver(instant))

    def resample(self, onto: Sampling) -> Point3Signal:
        """This signal reconstructed onto a new time base."""
        return _ResampledPoint3Signal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap) -> Point3Signal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedPoint3Signal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> Point3Signal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedPoint3Signal(source=self, to=window)

    def shift(self, by: Duration | float) -> Point3Signal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))

    def displacement_to(self, other: Point3Signal) -> Vec3Signal:
        """The vector from this trajectory to ``other`` over time (→ ``Vec3Signal``), time-aligned."""
        return _DisplacementVec3Signal(a=self, b=other)

    def distance_to(self, other: Point3Signal) -> ScalarSignal:
        """The distance between this trajectory and ``other`` over time (→ ``ScalarSignal``), time-aligned."""
        return _DistanceScalarSignal(a=self, b=other)


@dataclass(frozen=True, eq=False)
class _SampledPoint3Signal(Point3Signal):
    """Grounds each point sample (the frame partiality) before building the series."""

    sampling: Sampling
    points: tuple[Point3, ...]
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        match self.sampling.decide():
            case Resolvable(base):
                if len(self.points) != base.count:
                    return Unresolvable(f"{len(self.points)} values for {base.count} sample times")
                grounded = gather(point.decide() for point in self.points)
                if isinstance(grounded, Unresolvable):
                    return grounded
                return Resolvable(
                    SampledSeries(
                        base.times,
                        tuple(grounded.value),
                        self.interpolation,
                        self.boundary,
                        POINT3_BLEND,
                        support_from_times(base.times, self.max_gap),
                    )
                )
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _ResampledPoint3Signal(Point3Signal):
    source: Point3Signal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedPoint3Signal(Point3Signal):
    source: Point3Signal
    by: TimeMap

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedPoint3Signal(Point3Signal):
    source: Point3Signal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _DisplacementVec3Signal(Vec3Signal):
    """The world-frame displacement between two point trajectories — a ``Vec3Signal``."""

    a: Point3Signal
    b: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t).displacement_to(self.b.at(t)), VEC3_BLEND)


@dataclass(frozen=True, eq=False)
class _DistanceScalarSignal(ScalarSignal):
    """The distance between two point trajectories over time — a ``ScalarSignal``."""

    a: Point3Signal
    b: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(self.a, self.b, lambda t: self.a.at(t).distance_to(self.b.at(t)), SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _Point3SampleAt(Point3):
    signal: Point3Signal
    instant: Instant

    def _decide(self) -> Point3Decision:
        return decide_sample(self.signal, self.instant)
