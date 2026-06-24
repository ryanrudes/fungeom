"""``Point3BundleSignal`` — a point cloud that varies over time (``Signal[Bundle[Point3]]``).

The composition payoff of the whole design: a *collection over time* is **not** a new
type — it is a ``Signal`` whose value is a ``Bundle``. The generic, value-agnostic
signal core hosts it directly once the bundle supplies a :class:`Blend`; under *linear*
reconstruction the blend interpolates two frames **key by key** (a world-space lerp over
the keys present in *both*), so a marker that drops out between frames is simply *absent*
in the interpolation. The ``(T, N)`` occlusion mask thus falls out of ``Coverage`` (time)
× the per-frame entity mask — no bespoke machinery. (An exact sample always returns that
frame's cloud unchanged; ``Boundary.hold``/``nearest`` *select* a whole bracketing cloud
rather than blending, so an occluded marker present in the selected bracket is returned.)

``at(t)`` bridges back to the static :class:`Bundle` algebra (``at(t).at(k)``,
``at(t).centroid()``); ``over`` / ``support`` / ``resample`` / ``restrict`` / ``shift``
/ ``reparameterize`` are inherited from the V-agnostic core unchanged. This lives in the
*signals* package because the dependency edge runs ``signal → bundle`` (a signal may
host a bundle value; the base bundle layer never imports signals).
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.point3.resolvers.base import Point3
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.sampling.value import TimeSeries, as_times
from fungeom.primitives.signals.blend import Blend
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.point3 import POINT3_BLEND, Point3Signal
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    decide_warped,
    support_from_times,
)
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp
from fungeom.primitives.vec3.value import as_vec3


class _Point3BundleBlend:
    """World-space linear interpolation of two point clouds, key by key.

    Total: interpolates exactly the keys present in *both* frames (over the shared
    declared roster), so a marker absent in either bracket is absent in the result —
    the entity half of the occlusion mask. The points are already world-anchored.
    """

    def between(
        self,
        a: BundleValue[Point3Value],
        b: BundleValue[Point3Value],
        frac: float,
    ) -> Resolvability[BundleValue[Point3Value]]:
        members: dict[Hashable, Point3Value] = {}
        for key in a.roster:
            if a.present(key) and b.present(key):
                va, vb = a.members[key], b.members[key]
                members[key] = Point3Value(coord=as_vec3(va.coord + frac * (vb.coord - va.coord)), frame=WORLD_FRAME)
        return Resolvable(BundleValue(roster=a.roster, members=members))


POINT3_BUNDLE_BLEND = _Point3BundleBlend()


def _distributed_support(present: list[int], times: TimeSeries, base: CoverageValue) -> CoverageValue:
    """The support of one key's extracted trajectory — split at every gap it should have.

    Two *adjacent* present frames are joined only when the cloud signal connects them
    (they fall in one span of ``base``); an intervening occluded frame, or a temporal
    dropout, splits the support. So the projection gaps out exactly where the cloud's
    own ``at(t).at(key)`` would — an interior segment is defined only when the marker
    is present at *both* bracketing frames. An isolated present frame is a point span.
    """

    def connected(a: int, b: int) -> bool:
        ta, tb = float(times[a]), float(times[b])
        return b == a + 1 and any(span.start <= ta and tb <= span.end for span in base.intervals)

    spans: list[IntervalValue] = []
    run_start = previous = present[0]
    for index in present[1:]:
        if connected(previous, index):
            previous = index
            continue
        spans.append(IntervalValue(start=float(times[run_start]), end=float(times[previous])))
        run_start = previous = index
    spans.append(IntervalValue(start=float(times[run_start]), end=float(times[previous])))
    return CoverageValue(tuple(spans))


def decide_distributed[V](
    source: Signal[BundleValue[V]],
    key: Hashable,
    blend: Blend[V],
) -> Resolvability[SampledSeries[V]]:
    """Project one key's trajectory out of a cloud signal — the entity-axis slice (``distribute``).

    The dual of sampling: ``source.at(t)`` slices the cloud at one *instant*; this
    slices one *entity* across all time, into a plain ``Signal[V]``. Its samples are
    ``key``'s value at the frames where it is present, and its support gaps out
    wherever ``key`` is occluded (see :func:`_distributed_support`), so it is
    Unresolvable exactly where ``source.at(t).at(key)`` is — the commuting square
    holds on the support. Unresolvable if ``source`` is, if ``key`` is not in the
    cloud's roster, or if ``key`` is declared but never present (a fully-occluded
    marker has no trajectory to project).
    """
    decided = source.decide()
    if isinstance(decided, Unresolvable):
        return decided
    series = decided.value
    if series.interpolation is not Interpolation.linear or series.boundary is not Boundary.undefined:
        # The present-frames-only projection commutes with at(t).at(key) only under the
        # default reconstruction: hold/nearest *select* a whole bracket (so an occluded
        # marker in it is still read), and hold/wrap clamp against the projection's own
        # hull (≠ the cloud's). Both break the square, so we refuse rather than disagree.
        return Unresolvable(
            "key() requires the cloud signal's default reconstruction (linear interpolation, "
            "undefined boundary) — the configuration where the entity-axis slice provably "
            "commutes with at(t)"
        )
    if series.values and key not in series.values[0].roster:
        return Unresolvable(f"key {key!r} is not in the cloud signal's roster")
    present = [index for index, cloud in enumerate(series.values) if cloud.present(key)]
    if not present:
        return Unresolvable(f"key {key!r} is never present in the cloud signal")
    times = as_times([float(series.times[index]) for index in present])
    values = tuple(series.values[index].at(key) for index in present)
    support = _distributed_support(present, series.times, series.support)
    return Resolvable(SampledSeries(times, values, series.interpolation, series.boundary, blend, support))


class Point3BundleSignal(Signal[BundleValue[Point3Value]]):
    """A deferred point cloud over time — the trajectory of a whole marker set.

    Build with :meth:`from_frames` (a ``(T, N, 3)`` array of positions over a time
    base, with an optional ``(T, N)`` presence mask for per-frame occlusion). Sample
    with :meth:`at` (→ a rich :class:`~fungeom.Point3Bundle`); ``resolve()`` yields a
    ``SampledSeries`` of clouds. The temporal ops (:meth:`over`, :meth:`support`,
    :meth:`resample`, :meth:`restrict`, :meth:`shift`, :meth:`reparameterize`) are
    inherited from the generic signal core.
    """

    type Value = SampledSeries[BundleValue[Point3Value]]
    """The resolved value type — a ``SampledSeries`` of world-anchored point clouds."""

    @classmethod
    def from_frames(
        cls,
        times: ArrayLike,
        frames: ArrayLike,
        keys: Sequence[Hashable] | None = None,
        frame: CoordinateFrame | Frame = WORLD_FRAME,
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
        present: ArrayLike | None = None,
    ) -> Point3BundleSignal:
        """A cloud signal from ``(T, N, 3)`` positions over ``times`` (keyed by ``keys``).

        With a ``(T, N)`` boolean ``present`` mask, a key absent in a frame is occluded
        there: an exact sample of that frame omits it, and a *linear* interpolation
        across the dropout leaves it absent (``hold``/``nearest`` instead return the
        selected bracketing cloud, so a marker present there is carried across).
        ``max_gap`` marks *temporal* dropouts the same way the other signals do. Samples
        are world-anchored at build, so an ungrounded ``frame`` is Unresolvable.
        """
        data = np.array(frames, dtype=float)  # copy; expected shape (T, N, 3)
        member_keys = tuple(keys) if keys is not None else tuple(range(data.shape[1]))
        mask = None if present is None else np.array(present, dtype=bool)  # copy
        return _SampledPoint3BundleSignal(
            sampling=Sampling.at_times(times),
            frames=data,
            member_keys=member_keys,
            frame=frame,
            present=mask,
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    def at(self, instant: Instant | float) -> Point3Bundle:
        """The cloud at ``instant`` (→ ``Point3Bundle``); off-domain / in a gap is Unresolvable."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _Point3BundleSampleAt(signal=self, instant=as_instant_resolver(instant))

    def key(self, marker: Hashable) -> Point3Signal:
        """One marker's trajectory over time (→ ``Point3Signal``) — the *entity-axis* slice.

        The transpose of :meth:`at`: where ``at(t)`` slices the whole cloud at one
        *instant*, ``key(k)`` slices one marker across *all* time. This is the single
        column of ``distribute`` (``Signal[Bundle] → Bundle[Signal]``). The result is
        an ordinary :class:`~fungeom.Point3Signal`, so the full trajectory algebra is
        available (``key("HEAD").distance_to(key("LWRIST"))`` is a ``ScalarSignal``).

        Its support gaps out wherever the marker is occluded — Unresolvable on a
        segment unless the marker is present at *both* bracketing frames (mirroring the
        cloud blend's key-intersection) and at an occluded exact frame — so the
        commuting square ``signal.at(t).at(k) == signal.key(k).at(t)`` holds on the
        support. Unresolvable to build if ``k`` is not in the cloud's roster, or is
        declared but never present (a fully-occluded marker has no trajectory).

        The square is proven only under the **default reconstruction** — linear
        interpolation and the ``undefined`` boundary — so a cloud signal built with a
        ``hold``/``nearest`` kernel or a ``hold``/``wrap`` boundary (whose *select*/clamp
        semantics the present-frames projection cannot mirror) makes ``key`` Unresolvable
        rather than silently disagree.
        """
        return _DistributedPoint3Signal(source=self, marker=marker)

    def resample(self, onto: Sampling) -> Point3BundleSignal:
        """This cloud signal reconstructed onto a new time base."""
        return _ResampledPoint3BundleSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> Point3BundleSignal:
        """This cloud signal's time base warped ``by`` a map (shift / scale / reverse / warp)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedPoint3BundleSignal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedPoint3BundleSignal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> Point3BundleSignal:
        """Narrow this cloud signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedPoint3BundleSignal(source=self, to=window)

    def shift(self, by: Duration | float) -> Point3BundleSignal:
        """This cloud signal translated in time by ``by``."""
        return self.reparameterize(TimeMap.shift(by))


@dataclass(frozen=True, eq=False)
class _SampledPoint3BundleSignal(Point3BundleSignal):
    """Builds a world-anchored cloud per frame (respecting the presence mask) before the series."""

    sampling: Sampling
    frames: np.ndarray
    member_keys: tuple[Hashable, ...]
    frame: CoordinateFrame | Frame
    present: np.ndarray | None
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        match self.sampling.decide():
            case Resolvable(base):
                if self.frames.shape[0] != base.count:
                    return Unresolvable(f"{self.frames.shape[0]} frames for {base.count} sample times")
                clouds: list[BundleValue[Point3Value]] = []
                for ti in range(base.count):
                    members: dict[Hashable, Point3Value] = {}
                    for ni, key in enumerate(self.member_keys):
                        if self.present is None or bool(self.present[ti, ni]):
                            x, y, z = self.frames[ti, ni]
                            decided = Point3.at(float(x), float(y), float(z), frame=self.frame).decide()
                            if isinstance(decided, Unresolvable):
                                return decided
                            members[key] = decided.value
                    clouds.append(BundleValue(roster=self.member_keys, members=members))
                return Resolvable(
                    SampledSeries(
                        base.times,
                        tuple(clouds),
                        self.interpolation,
                        self.boundary,
                        POINT3_BUNDLE_BLEND,
                        support_from_times(base.times, self.max_gap),
                    )
                )
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _Point3BundleSampleAt(Point3Bundle):
    """The cloud sampled at one instant — bridges back to the static Bundle algebra."""

    signal: Point3BundleSignal
    instant: Instant

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_sample(self.signal, self.instant)


@dataclass(frozen=True, eq=False)
class _DistributedPoint3Signal(Point3Signal):
    """One marker's trajectory projected out of a cloud signal — bridges to the Point3Signal algebra."""

    source: Point3BundleSignal
    marker: Hashable

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_distributed(self.source, self.marker, POINT3_BLEND)


@dataclass(frozen=True, eq=False)
class _ResampledPoint3BundleSignal(Point3BundleSignal):
    source: Point3BundleSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedPoint3BundleSignal(Point3BundleSignal):
    source: Point3BundleSignal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedPoint3BundleSignal(Point3BundleSignal):
    source: Point3BundleSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_restricted(self.source, self.to)
