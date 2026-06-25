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

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

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
    decide_derivative,
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
from fungeom.primitives.signals.transform import TransformSignal
from fungeom.primitives.signals.vec3 import VEC3_BLEND, Vec3Signal
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp
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

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> Point3Signal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedPoint3Signal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedPoint3Signal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> Point3Signal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedPoint3Signal(source=self, to=window)

    def shift(self, by: Duration | float) -> Point3Signal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        """Resample onto ``onto`` and resolve to a raw ``(T, 3) array`` — the vectorized readback.

        The sanctioned exit into numpy; resolves eagerly (raises ``UnresolvableError`` if a
        target is off the support).
        """
        return resolved_rows(self.resample(onto), lambda value: value.coord)

    def displacement_to(self, other: Point3Signal) -> Vec3Signal:
        """The vector from this trajectory to ``other`` over time (→ ``Vec3Signal``), time-aligned."""
        return _DisplacementVec3Signal(a=self, b=other)

    def distance_to(self, other: Point3Signal) -> ScalarSignal:
        """The distance between this trajectory and ``other`` over time (→ ``ScalarSignal``), time-aligned."""
        return _DistanceScalarSignal(a=self, b=other)

    def velocity(self) -> Vec3Signal:
        """The finite-difference velocity — the time derivative of position (→ ``Vec3Signal``).

        Exact central differences on the sample grid; Unresolvable with fewer than two samples.
        """
        return _VelocityVec3Signal(source=self)

    def speed(self) -> ScalarSignal:
        """The instantaneous speed over time — ``velocity().norm()`` (→ ``ScalarSignal``)."""
        return self.velocity().norm()

    @classmethod
    def lift(cls, sources: Sequence[Signal[Any]], combine: Callable[..., Point3]) -> Point3Signal:
        """Build a position signal by combining ``sources`` per instant (the general escape hatch)."""
        return _LiftedPoint3Signal(sources=tuple(sources), combine=combine)

    def map(self, transform: Callable[[Point3], Point3]) -> Point3Signal:
        """Apply ``transform`` to this trajectory at each instant (→ ``Point3Signal``; the unary lift)."""
        return _LiftedPoint3Signal(sources=(self,), combine=transform)

    def transformed_by(self, pose: TransformSignal) -> Point3Signal:
        """This trajectory carried through a moving ``pose`` over time (→ ``Point3Signal``).

        The transport lift: each instant's point is rigidly moved by that instant's pose
        (time-aligned on the union of their samples ∩ supports). Defined only where *both* are —
        off the pose's support or an ungrounded point is ``Unresolvable``. This is how a marker
        fixed in a moving body frame becomes a world trajectory.
        """
        return _TransformedPoint3Signal(a=self, pose=pose)


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
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
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
class _TransformedPoint3Signal(Point3Signal):
    """A point trajectory carried through a moving pose over time — the transport lift."""

    a: Point3Signal
    pose: TransformSignal

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_lifted(self.a, self.pose, lambda t: self.a.at(t).transformed_by(self.pose.at(t)), POINT3_BLEND)


@dataclass(frozen=True, eq=False)
class _LiftedPoint3Signal(Point3Signal):
    """A position signal built by combining N sources per instant — the general lift / map."""

    sources: tuple[Signal[Any], ...]
    combine: Callable[..., Point3]

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_lifted_n(self.sources, lambda t: self.combine(*(s.at(t) for s in self.sources)), POINT3_BLEND)


@dataclass(frozen=True, eq=False)
class _VelocityVec3Signal(Vec3Signal):
    """The finite-difference velocity of a position trajectory — a ``Vec3Signal``."""

    source: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        return decide_derivative(self.source, lambda a, b, dt: as_vec3((b.coord - a.coord) / dt), VEC3_BLEND)


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
