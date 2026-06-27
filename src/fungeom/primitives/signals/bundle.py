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

from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import overload

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.fit import fit_plane_coords, orient_plane_track
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle
from fungeom.primitives.bundle.resolvers.transform import TransformBundle
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.coverage.value import CoverageValue
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.frame.resolvers.base import Frame
from fungeom.primitives.frame.value import WORLD_FRAME, CoordinateFrame
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.plane.value import PlaneValue
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
    decide_lifted,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    decide_warped,
    resolved_grid,
    support_from_times,
)
from fungeom.primitives.signals.plane import PLANE_BLEND, PlaneSignal
from fungeom.primitives.signals.scalar import SCALAR_BLEND, ScalarSignal
from fungeom.primitives.signals.transform import TRANSFORM_BLEND, TransformSignal
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform
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

    @overload
    def transformed_by(self, pose: TransformSignal) -> Point3BundleSignal: ...
    @overload
    def transformed_by(self, pose: TransformBundleSignal) -> Point3BundleSignal: ...
    def transformed_by(self, pose: TransformSignal | TransformBundleSignal) -> Point3BundleSignal:
        """Carry the cloud through a moving ``pose`` over time (→ ``Point3BundleSignal``).

        A single ``TransformSignal`` moves every present marker by that instant's shared pose
        (the rigid-body case); a ``TransformBundleSignal`` moves each marker by its *own* joint's
        pose, **key by key** — the modeled-marker path. Time-aligned ∩ supports; off the pose's
        support → ``Unresolvable``.
        """
        if isinstance(pose, TransformBundleSignal):
            return _PerJointTransformedPoint3BundleSignal(a=self, poses=pose)
        return _TransformedPoint3BundleSignal(a=self, pose=pose)

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """Resample onto ``onto`` and resolve to a dense ``(T, N, 3)`` array + ``(T, N)`` present mask.

        The vectorized cloud readback: columns follow the roster, an occluded cell is ``nan`` with
        a ``False`` mask. Resolves eagerly (raises if a target is off the support).
        """
        return resolved_grid(self.resample(onto), lambda value: value.coord, np.full(3, np.nan))

    def fit_plane(self, *, tolerance: float = 1e-6) -> PlaneSignal:
        """The least-squares plane fitted to the cloud at every frame (→ ``PlaneSignal``).

        The **moving patch surface** — a batched per-frame SVD fit (the over-time companion to
        the static ``Point3Bundle.fit_plane``). Consecutive normals are oriented to agree (the
        per-frame SVD sign is arbitrary), so the plane track is continuous and its slerp blend
        well-posed. Strict: a frame whose cloud is degenerate (fewer than three present points,
        near-collinear, or isotropic) makes the whole signal ``Unresolvable``.
        """
        return _FittedPlaneSignal(source=self, tolerance=tolerance)

    def centroid(self) -> Point3Signal:
        """The cloud's centroid at every frame (→ ``Point3Signal``) — the CoM / cluster-centre track.

        The over-time companion to the static ``Point3Bundle.centroid`` (mean of the *present*
        members, world-anchored); read the same way the source is. A frame with no present member
        makes the whole signal ``Unresolvable``.
        """
        return _BundleCentroidPoint3Signal(source=self)


@dataclass(frozen=True, eq=False)
class _BundleCentroidPoint3Signal(Point3Signal):
    """The per-frame centroid of a moving point cloud — a ``Point3Signal`` of cloud centres."""

    source: Point3BundleSignal

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        decided = self.source.decide()
        if isinstance(decided, Unresolvable):
            return decided
        series = decided.value
        centres: list[Point3Value] = []
        for frame in series.values:
            present = [frame.members[key] for key in frame.support()]
            if not present:
                return Unresolvable("the centroid is undefined at a frame with no present members")
            mean = np.mean([member.coord for member in present], axis=0)
            centres.append(Point3Value(coord=mean, frame=WORLD_FRAME))
        return Resolvable(
            SampledSeries(
                series.times, tuple(centres), series.interpolation, series.boundary, POINT3_BLEND, series.support
            )
        )


@dataclass(frozen=True, eq=False)
class _TransformedPoint3BundleSignal(Point3BundleSignal):
    """A point cloud carried through one moving pose over time — the transport lift."""

    a: Point3BundleSignal
    pose: TransformSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_lifted(
            self.a, self.pose, lambda t: self.a.at(t).transformed_by(self.pose.at(t)), POINT3_BUNDLE_BLEND
        )


@dataclass(frozen=True, eq=False)
class _PerJointTransformedPoint3BundleSignal(Point3BundleSignal):
    """A point cloud carried through per-joint moving poses over time — the modeled-marker path."""

    a: Point3BundleSignal
    poses: TransformBundleSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_lifted(
            self.a, self.poses, lambda t: self.a.at(t).transformed_by(self.poses.at(t)), POINT3_BUNDLE_BLEND
        )


@dataclass(frozen=True, eq=False)
class _FittedPlaneSignal(PlaneSignal):
    """A plane fitted per frame to a moving point cloud — the moving patch surface."""

    source: Point3BundleSignal
    tolerance: float

    def _decide(self) -> Resolvability[SampledSeries[PlaneValue]]:
        decided = self.source.decide()
        if isinstance(decided, Unresolvable):
            return decided
        series = decided.value
        raw: list[PlaneValue] = []
        for frame in series.values:
            coords = np.array([frame.members[key].coord for key in frame.support()])
            fit = fit_plane_coords(coords, self.tolerance)
            if isinstance(fit, Unresolvable):
                return Unresolvable(f"plane fit failed at a frame: {fit.reason}")
            raw.append(fit.value)
        planes = orient_plane_track(raw)
        return Resolvable(
            SampledSeries(
                series.times, tuple(planes), series.interpolation, series.boundary, PLANE_BLEND, series.support
            )
        )


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


class _TransformBundleBlend:
    """Geodesic blend of two pose-sets on SE(3), key by key — the elementwise lift of ``TRANSFORM_BLEND``.

    Each key present in *both* frames is slerped (rotation) + lerped (translation) by the
    same SE(3) blend a ``TransformSignal`` uses; a key absent in either bracket is absent
    in the result (the entity half of the occlusion mask). **Strict over op-failure:** if
    any present-in-both key is an opposed-orientation pair (no unique geodesic), the *whole*
    interpolated pose-set is ``Unresolvable`` — an op-failure is never silently turned into
    absence (the mask carries *data presence* only, never reconstruction failure). This is
    the one way the partial SE(3) blend differs from the total ``Point3`` lerp, and it is
    why ``TransformBundleSignal`` offers no ``key`` projection (see the class docstring).
    """

    def between(
        self,
        a: BundleValue[RigidTransform],
        b: BundleValue[RigidTransform],
        frac: float,
    ) -> Resolvability[BundleValue[RigidTransform]]:
        members: dict[Hashable, RigidTransform] = {}
        for key in a.roster:
            if a.present(key) and b.present(key):
                decided = TRANSFORM_BLEND.between(a.members[key], b.members[key], frac)
                if isinstance(decided, Unresolvable):
                    return decided
                members[key] = decided.value
        return Resolvable(BundleValue(roster=a.roster, members=members))


TRANSFORM_BUNDLE_BLEND = _TransformBundleBlend()


class TransformBundleSignal(Signal[BundleValue[RigidTransform]]):
    """A deferred set of rigid poses over time — a skeleton's joints (``Signal[Bundle[Transform]]``).

    The rotation-over-time companion to :class:`Point3BundleSignal`: where that carries a
    point cloud, this carries a *pose-set* — every joint's full SE(3) pose at each frame,
    the natural home for mocap ``(T, N, 3, 3)`` / ``(T, N, 4)`` joint rotations. Build with
    :meth:`from_frames` (a ``(T, N)`` grid of ``Transform`` poses over a time base, with an
    optional ``(T, N)`` presence mask for per-frame occlusion); sample with :meth:`at`
    (→ a rich :class:`~fungeom.TransformBundle`). The temporal ops (:meth:`over`,
    :meth:`support`, :meth:`resample`, :meth:`restrict`, :meth:`shift`,
    :meth:`reparameterize`) are inherited from the V-agnostic core unchanged.

    Reconstruction is the elementwise SE(3) blend (slerp + lerp). Unlike the total
    ``Point3`` lerp this blend is **partial** — interpolating across opposed orientations
    is ``Unresolvable`` — and it is *strict over that op-failure*: one antipodal joint makes
    the whole interpolated pose-set ``Unresolvable`` (an op-failure is never disguised as
    absence). That strictness is exactly why there is **no** ``key`` projection here: the
    entity-axis slice ``key(k).at(t)`` would depend only on ``k`` while ``at(t).at(k)``
    depends on *every* joint (the whole-cloud blend), so the commuting square cannot hold —
    a general delegating ``key`` is a documented follow-on. Query a single joint at an
    instant with ``at(t).at(k)``.
    """

    type Value = SampledSeries[BundleValue[RigidTransform]]
    """The resolved value type — a ``SampledSeries`` of rigid pose-sets."""

    @classmethod
    def from_frames(
        cls,
        times: ArrayLike,
        frames: Sequence[Sequence[Transform]],
        keys: Sequence[Hashable] | None = None,
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
        present: ArrayLike | None = None,
    ) -> TransformBundleSignal:
        """A pose-set signal from a ``(T, N)`` grid of ``Transform`` poses over ``times``.

        Each row is one frame's ``N`` joint poses (keyed by ``keys`` or by position).
        Construction is **strict**: every present pose is resolved at build, so a partial
        member (e.g. a degenerate-axis rotation) makes the whole signal ``Unresolvable``.
        A ``(T, N)`` boolean ``present`` mask marks per-frame occlusion (an absent joint is
        omitted from that frame's pose-set, and a *linear* interpolation across the dropout
        leaves it absent); ``max_gap`` marks *temporal* dropouts as the other signals do.
        A ``RigidTransform`` value is wrapped with ``Transform.known``.
        """
        rows = tuple(tuple(row) for row in frames)
        width = len(rows[0]) if rows else 0
        member_keys = tuple(keys) if keys is not None else tuple(range(width))
        mask = None if present is None else np.array(present, dtype=bool)  # copy
        return _SampledTransformBundleSignal(
            sampling=Sampling.at_times(times),
            frames=rows,
            member_keys=member_keys,
            present=mask,
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    def at(self, instant: Instant | float) -> TransformBundle:
        """The pose-set at ``instant`` (→ ``TransformBundle``); off-domain / in a gap / across opposed orientations is Unresolvable."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _TransformBundleSampleAt(signal=self, instant=as_instant_resolver(instant))

    def key(self, joint: Hashable) -> TransformSignal:
        """One joint's pose trajectory over time (→ ``TransformSignal``) — the *entity-axis* slice.

        The transpose of :meth:`at` (which slices the whole pose-set at one instant): ``key(j)``
        pulls one joint's pose across all time, as an ordinary ``TransformSignal`` (so the segment
        runtime can transport a patch by ``poses.key("shin")``). Its support gaps out where the
        joint is occluded, so the commuting square ``at(t).at(j) == key(j).at(t)`` holds on the
        support (both reconstruct by the same slerp — Unresolvable together across opposed
        orientations). Unresolvable to build if ``j`` is absent from the roster or never present.
        """
        return _DistributedTransformSignal(source=self, joint=joint)

    def resample(self, onto: Sampling) -> TransformBundleSignal:
        """This pose-set signal reconstructed onto a new time base."""
        return _ResampledTransformBundleSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> TransformBundleSignal:
        """This pose-set signal's time base warped ``by`` a map (shift / scale / reverse / warp)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedTransformBundleSignal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedTransformBundleSignal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> TransformBundleSignal:
        """Narrow this pose-set signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedTransformBundleSignal(source=self, to=window)

    def shift(self, by: Duration | float) -> TransformBundleSignal:
        """This pose-set signal translated in time by ``by``."""
        return self.reparameterize(TimeMap.shift(by))


@dataclass(frozen=True, eq=False)
class _DistributedTransformSignal(TransformSignal):
    """One joint's pose trajectory projected out of a pose-set signal — bridges to TransformSignal."""

    source: TransformBundleSignal
    joint: Hashable

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        return decide_distributed(self.source, self.joint, TRANSFORM_BLEND)


@dataclass(frozen=True, eq=False)
class _SampledTransformBundleSignal(TransformBundleSignal):
    """Resolves each frame's pose-set (respecting the presence mask) before the series."""

    sampling: Sampling
    frames: tuple[tuple[Transform, ...], ...]
    member_keys: tuple[Hashable, ...]
    present: np.ndarray | None
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        match self.sampling.decide():
            case Resolvable(base):
                if len(self.frames) != base.count:
                    return Unresolvable(f"{len(self.frames)} frames for {base.count} sample times")
                poses: list[BundleValue[RigidTransform]] = []
                for ti in range(base.count):
                    row = self.frames[ti]
                    if len(row) != len(self.member_keys):
                        return Unresolvable(f"frame {ti} has {len(row)} poses for {len(self.member_keys)} keys")
                    members: dict[Hashable, RigidTransform] = {}
                    for ni, key in enumerate(self.member_keys):
                        if self.present is None or bool(self.present[ti, ni]):
                            decided = row[ni].decide()
                            if isinstance(decided, Unresolvable):
                                return decided
                            members[key] = decided.value
                    poses.append(BundleValue(roster=self.member_keys, members=members))
                return Resolvable(
                    SampledSeries(
                        base.times,
                        tuple(poses),
                        self.interpolation,
                        self.boundary,
                        TRANSFORM_BUNDLE_BLEND,
                        support_from_times(base.times, self.max_gap),
                    )
                )
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _TransformBundleSampleAt(TransformBundle):
    """The pose-set sampled at one instant — bridges back to the static Bundle algebra."""

    signal: TransformBundleSignal
    instant: Instant

    def _decide(self) -> BundleDecision[RigidTransform]:
        return decide_sample(self.signal, self.instant)


@dataclass(frozen=True, eq=False)
class _ResampledTransformBundleSignal(TransformBundleSignal):
    source: TransformBundleSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedTransformBundleSignal(TransformBundleSignal):
    source: TransformBundleSignal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedTransformBundleSignal(TransformBundleSignal):
    source: TransformBundleSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        return decide_restricted(self.source, self.to)


# --- ScalarBundleSignal (T9) — a collection of scalars over time, with per-instant folds ---


class _ScalarBundleBlend:
    """Key-by-key linear interpolation of two scalar clouds (over the keys present in both)."""

    def between(self, a: BundleValue[float], b: BundleValue[float], frac: float) -> Resolvability[BundleValue[float]]:
        members: dict[Hashable, float] = {}
        for key in a.roster:
            if a.present(key) and b.present(key):
                members[key] = a.members[key] + frac * (b.members[key] - a.members[key])
        return Resolvable(BundleValue(roster=a.roster, members=members))


SCALAR_BUNDLE_BLEND = _ScalarBundleBlend()


def decide_folded[U](
    source: Signal[BundleValue[float]],
    fold: Callable[[BundleValue[float]], Resolvability[U]],
    blend: Blend[U],
) -> Resolvability[SampledSeries[U]]:
    """Reduce each frame of a scalar-cloud signal to one value — a per-instant fold (→ ``Signal[U]``).

    ``fold`` collapses one frame's bundle (e.g. the minimum over its present members); a frame
    whose fold is ``Unresolvable`` (a fold over no present members) makes the whole signal so.
    The result is sampled at the same instants over the same support and **reconstructed the same
    way the source is** — the per-frame fold commutes with the source's interpolation/boundary
    (a held frame's fold is the held folded value), so a ``hold``/``nearest``/``wrap`` or
    hold-boundary cloud signal folds to a signal read the same way, rather than silently
    snapping to linear/undefined (which would disagree with ``at(t)`` and shrink the domain).
    """
    decided = source.decide()
    if isinstance(decided, Unresolvable):
        return decided
    series = decided.value
    out: list[U] = []
    for frame in series.values:
        reduced = fold(frame)
        if isinstance(reduced, Unresolvable):
            return Unresolvable(f"fold is undefined at a frame: {reduced.reason}")
        out.append(reduced.value)
    return Resolvable(
        SampledSeries(series.times, tuple(out), series.interpolation, series.boundary, blend, series.support)
    )


def _present_values(frame: BundleValue[float]) -> list[float]:
    return [frame.members[key] for key in frame.support()]


class ScalarBundleSignal(Signal[BundleValue[float]]):
    """A deferred collection of scalars over time — e.g. per-marker clearance over a clip.

    Build with :meth:`from_frames` (a ``(T, N)`` array with an optional ``(T, N)`` presence
    mask); sample with :meth:`at` (→ a ``ScalarBundle``). The folds reduce the cloud *per
    instant* to a plain ``ScalarSignal`` — :meth:`min` / :meth:`max` / :meth:`mean` / :meth:`sum`
    / :meth:`count` — so a footprint's min-clearance-over-time is ``clearances.min()``, and "any
    corner in contact" is ``clearances.min().le(0)`` (a ``BoolSignal``). Temporal ops are
    inherited from the generic core.
    """

    type Value = SampledSeries[BundleValue[float]]
    """The resolved value type — a ``SampledSeries`` of scalar clouds."""

    @classmethod
    def from_frames(
        cls,
        times: ArrayLike,
        frames: ArrayLike,
        keys: Sequence[Hashable] | None = None,
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
        present: ArrayLike | None = None,
    ) -> ScalarBundleSignal:
        """A scalar-cloud signal from a ``(T, N)`` array over ``times`` (keyed by ``keys``).

        With a ``(T, N)`` ``present`` mask a key absent in a frame is occluded there (omitted
        from that frame's bundle); ``max_gap`` marks temporal dropouts as for the other signals.
        """
        data = np.array(frames, dtype=float)  # copy; expected shape (T, N)
        member_keys = tuple(keys) if keys is not None else tuple(range(data.shape[1]))
        mask = None if present is None else np.array(present, dtype=bool)
        return _SampledScalarBundleSignal(
            sampling=Sampling.at_times(times),
            frames=data,
            member_keys=member_keys,
            present=mask,
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    def at(self, instant: Instant | float) -> ScalarBundle:
        """The scalar cloud at ``instant`` (→ ``ScalarBundle``; bridges to the static algebra)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _ScalarBundleSampleAt(signal=self, instant=as_instant_resolver(instant))

    def min(self) -> ScalarSignal:
        """The per-instant minimum over the present members (→ ``ScalarSignal``; empty frame → Unresolvable)."""
        return _FoldedScalarSignal(source=self, kind="min")

    def max(self) -> ScalarSignal:
        """The per-instant maximum over the present members (→ ``ScalarSignal``; empty frame → Unresolvable)."""
        return _FoldedScalarSignal(source=self, kind="max")

    def mean(self) -> ScalarSignal:
        """The per-instant average over the present members (→ ``ScalarSignal``; empty frame → Unresolvable)."""
        return _FoldedScalarSignal(source=self, kind="mean")

    def sum(self) -> ScalarSignal:
        """The per-instant sum over the present members (→ ``ScalarSignal``; ``0`` over an empty frame)."""
        return _FoldedScalarSignal(source=self, kind="sum")

    def count(self) -> ScalarSignal:
        """The per-instant count of present members (→ ``ScalarSignal``; total)."""
        return _FoldedScalarSignal(source=self, kind="count")

    def resample(self, onto: Sampling) -> ScalarBundleSignal:
        """This signal reconstructed onto a new time base (Unresolvable if a target is undefined)."""
        return _ResampledScalarBundleSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> ScalarBundleSignal:
        """This signal's time base warped ``by`` a map (shift / scale / reverse / monotonic warp)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedScalarBundleSignal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedScalarBundleSignal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> ScalarBundleSignal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedScalarBundleSignal(source=self, to=window)

    def shift(self, by: Duration | float) -> ScalarBundleSignal:
        """This signal translated in time by ``by``."""
        return self.reparameterize(TimeMap.shift(by))

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """Resample onto ``onto`` and resolve to a dense ``(T, N)`` array + ``(T, N)`` present mask.

        The vectorized scalar-cloud readback (an occluded cell is ``nan`` with a ``False`` mask);
        resolves eagerly (raises if a target is off the support).
        """
        return resolved_grid(self.resample(onto), lambda value: value, np.nan)


_SCALAR_FOLDS: dict[str, Callable[[BundleValue[float]], Resolvability[float]]] = {
    "min": lambda frame: (
        Resolvable(min(_present_values(frame))) if frame.count else Unresolvable("min over an empty frame")
    ),
    "max": lambda frame: (
        Resolvable(max(_present_values(frame))) if frame.count else Unresolvable("max over an empty frame")
    ),
    "mean": lambda frame: (
        Resolvable(sum(_present_values(frame)) / frame.count)
        if frame.count
        else Unresolvable("mean over an empty frame")
    ),
    "sum": lambda frame: Resolvable(float(sum(_present_values(frame)))),
    "count": lambda frame: Resolvable(float(frame.count)),
}


@dataclass(frozen=True, eq=False)
class _SampledScalarBundleSignal(ScalarBundleSignal):
    sampling: Sampling
    frames: np.ndarray
    member_keys: tuple[Hashable, ...]
    present: np.ndarray | None
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        match self.sampling.decide():
            case Resolvable(base):
                if self.frames.shape[0] != base.count:
                    return Unresolvable(f"{self.frames.shape[0]} frames for {base.count} sample times")
                clouds: list[BundleValue[float]] = []
                for ti in range(base.count):
                    members: dict[Hashable, float] = {}
                    for ni, key in enumerate(self.member_keys):
                        if self.present is None or bool(self.present[ti, ni]):
                            members[key] = float(self.frames[ti, ni])
                    clouds.append(BundleValue(roster=self.member_keys, members=members))
                return Resolvable(
                    SampledSeries(
                        base.times,
                        tuple(clouds),
                        self.interpolation,
                        self.boundary,
                        SCALAR_BUNDLE_BLEND,
                        support_from_times(base.times, self.max_gap),
                    )
                )
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _ScalarBundleSampleAt(ScalarBundle):
    signal: ScalarBundleSignal
    instant: Instant

    def _decide(self) -> BundleDecision[float]:
        return decide_sample(self.signal, self.instant)


@dataclass(frozen=True, eq=False)
class _FoldedScalarSignal(ScalarSignal):
    """A scalar-cloud signal reduced per instant — min / max / mean / sum / count (→ ``ScalarSignal``)."""

    source: ScalarBundleSignal
    kind: str

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_folded(self.source, _SCALAR_FOLDS[self.kind], SCALAR_BLEND)


@dataclass(frozen=True, eq=False)
class _ResampledScalarBundleSignal(ScalarBundleSignal):
    source: ScalarBundleSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedScalarBundleSignal(ScalarBundleSignal):
    source: ScalarBundleSignal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedScalarBundleSignal(ScalarBundleSignal):
    source: ScalarBundleSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _PlaneClearanceBundleSignal(ScalarBundleSignal):
    """Per-marker signed distance from a moving cloud to a moving plane — the clearance field over time."""

    plane: PlaneSignal
    cloud: Point3BundleSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        return decide_lifted(
            self.plane, self.cloud, lambda t: self.plane.at(t).signed_distance(self.cloud.at(t)), SCALAR_BUNDLE_BLEND
        )

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """Resample onto ``onto`` and resolve to a dense ``(T, N)`` signed-distance array + present mask.

        The vectorized form of the per-instant lift: the moving plane's ``(points, normals)`` stacks
        dotted against the moving cloud in one batched op (occluded cells stay ``nan`` with a
        ``False`` mask). Resolves eagerly (raises if a target is off either support).
        """
        points, normals = self.plane._sampled_planes(onto)  # (T, 3), (T, 3)
        cloud, mask = self.cloud.resolve_over(onto)  # (T, N, 3), (T, N)
        values = np.einsum("tnc,tc->tn", cloud - points[:, None, :], normals)  # n · (qₖ − p₀)
        return np.where(mask, values, np.nan), mask
