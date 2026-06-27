"""``PlaneSignal`` — an oriented plane that varies over time (a moving patch surface).

A thin facade over the generic signal core for ``PlaneValue`` samples: its blend lerps the
representative point and **slerps the normal** (a direction on the sphere, so *partial* between
opposed normals — like ``Direction3Signal``). The over-time companion to the static ``Plane`` /
``Region2`` / ``Face`` patch work: a contact surface fitted to a moving marker cloud
(``Point3BundleSignal.fit_plane``) and read back as a normal track or a clearance signal.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

import numpy as np

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.plane.decidability import PlaneDecision
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.direction3 import DIRECTION3_BLEND, Direction3Signal
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.point3 import POINT3_BLEND, Point3Signal
from fungeom.primitives.signals.scalar import SCALAR_BLEND, ScalarSignal
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_lifted,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    decide_sampled,
    decide_signal_map,
    decide_warped,
)
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp

if TYPE_CHECKING:
    from fungeom.primitives.signals.bundle import Point3BundleSignal, ScalarBundleSignal

_PARALLEL = 1.0 - 1e-9


class _PlaneBlend:
    """Lerp the plane's point, slerp its normal — partial between opposed normals."""

    def between(self, a: PlaneValue, b: PlaneValue, frac: float) -> Resolvability[PlaneValue]:
        point = a.point + frac * (b.point - a.point)
        dot = float(np.clip(np.dot(a.normal, b.normal), -1.0, 1.0))
        if dot <= -_PARALLEL:
            return Unresolvable("no unique plane between opposed normals")
        if dot >= _PARALLEL:
            return Resolvable(PlaneValue(point=point, normal=a.normal))
        theta = float(np.arccos(dot))
        sin_theta = float(np.sin(theta))
        wa = float(np.sin((1.0 - frac) * theta)) / sin_theta
        wb = float(np.sin(frac * theta)) / sin_theta
        return Resolvable(PlaneValue(point=point, normal=wa * a.normal + wb * b.normal))


PLANE_BLEND = _PlaneBlend()


class PlaneSignal(Signal[PlaneValue]):
    """A deferred oriented plane that varies over time — a moving surface.

    Construct with :meth:`from_samples` / :meth:`sampled`, or fit one per frame with
    ``Point3BundleSignal.fit_plane``. Read with :meth:`at` (→ ``Plane``), :meth:`normal`
    (→ ``Direction3Signal``), :meth:`origin` (→ ``Point3Signal``), :meth:`signed_distance`
    (against a ``Point3Signal`` → ``ScalarSignal``), plus the inherited time-ops. The blend is
    *partial* — between opposed normals there is no unique plane.
    """

    type Value = SampledSeries[PlaneValue]
    """The resolved value type — a ``SampledSeries`` of oriented planes."""

    @classmethod
    def sampled(
        cls,
        sampling: Sampling,
        values: Sequence[PlaneValue],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> PlaneSignal:
        """A plane signal of ``values`` over ``sampling`` (read ``via`` a kernel, ``outside`` its ends)."""
        return _SampledPlaneSignal(
            sampling=sampling, values=tuple(values), interpolation=via, boundary=outside, max_gap=max_gap
        )

    @classmethod
    def from_samples(
        cls,
        times: ArrayLike,
        values: Sequence[PlaneValue],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> PlaneSignal:
        """A plane signal sampled at explicit ``times`` (sugar over :meth:`sampled`)."""
        return cls.sampled(Sampling.at_times(times), values, via=via, outside=outside, max_gap=max_gap)

    def at(self, instant: Instant | float) -> Plane:
        """The plane at ``instant`` (→ ``Plane``; Unresolvable off the domain or in a gap)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _PlaneSampleAt(signal=self, instant=as_instant_resolver(instant))

    def normal(self) -> Direction3Signal:
        """The plane's unit normal over time (→ ``Direction3Signal``)."""
        return _PlaneNormalSignal(source=self)

    def origin(self) -> Point3Signal:
        """The plane's representative point over time (→ ``Point3Signal``)."""
        return _PlaneOriginSignal(source=self)

    @overload
    def signed_distance(self, point: Point3Signal) -> ScalarSignal: ...
    @overload
    def signed_distance(self, point: Point3BundleSignal) -> ScalarBundleSignal: ...
    def signed_distance(self, point: Point3Signal | Point3BundleSignal) -> ScalarSignal | ScalarBundleSignal:
        """The signed distance from a moving ``point`` to this moving plane over time (→ ``ScalarSignal``).

        Broadcasts over a moving cloud (``Point3BundleSignal`` → ``ScalarBundleSignal``) — the
        per-marker clearance field over time, whose ``.min()`` is the footprint min-clearance.
        """
        from fungeom.primitives.signals.bundle import Point3BundleSignal, _PlaneClearanceBundleSignal

        if isinstance(point, Point3BundleSignal):
            return _PlaneClearanceBundleSignal(plane=self, cloud=point)
        return _PlaneSignedDistanceSignal(plane=self, point=point)

    def _sampled_planes(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """This plane's ``(points (T, 3), normals (T, 3))`` over ``onto`` — the vectorized readback hook.

        The base resolves per-instant (resample then stack); ``_FaceSignalPlane`` overrides it to
        transport the static plane by the materialized ``(T, 4, 4)`` pose stack in one batched op,
        so the moving-patch ``normal()`` / ``origin()`` / ``signed_distance`` readbacks that read
        through here all inherit the fast path. Resolves eagerly (raises off the support).
        """
        series = self.resample(onto).resolve()
        points = np.array([value.point for value in series.values], dtype=float).reshape(-1, 3)
        normals = np.array([value.normal for value in series.values], dtype=float).reshape(-1, 3)
        return points, normals

    def resample(self, onto: Sampling) -> PlaneSignal:
        """This signal reconstructed onto a new time base (Unresolvable if a target is undefined)."""
        return _ResampledPlaneSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> PlaneSignal:
        """This signal's time base warped ``by`` a map (shift / scale / reverse / monotonic warp)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedPlaneSignal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedPlaneSignal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> PlaneSignal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedPlaneSignal(source=self, to=window)

    def shift(self, by: Duration | float) -> PlaneSignal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))


@dataclass(frozen=True, eq=False)
class _SampledPlaneSignal(PlaneSignal):
    sampling: Sampling
    values: tuple[PlaneValue, ...]
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[PlaneValue]]:
        return decide_sampled(self.sampling, self.values, self.interpolation, self.boundary, PLANE_BLEND, self.max_gap)


@dataclass(frozen=True, eq=False)
class _ResampledPlaneSignal(PlaneSignal):
    source: PlaneSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[PlaneValue]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedPlaneSignal(PlaneSignal):
    source: PlaneSignal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[PlaneValue]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedPlaneSignal(PlaneSignal):
    source: PlaneSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[PlaneValue]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _PlaneSampleAt(Plane):
    signal: PlaneSignal
    instant: Instant

    def _decide(self) -> PlaneDecision:
        return decide_sample(self.signal, self.instant)


@dataclass(frozen=True, eq=False)
class _PlaneNormalSignal(Direction3Signal):
    source: PlaneSignal

    def _decide(self) -> Resolvability[SampledSeries[Direction3Value]]:
        return decide_signal_map(self.source, lambda p: Direction3Value(vector=p.normal), DIRECTION3_BLEND)

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        return self.source._sampled_planes(onto)[1]  # the (T, 3) normal stack


@dataclass(frozen=True, eq=False)
class _PlaneOriginSignal(Point3Signal):
    source: PlaneSignal

    def _decide(self) -> Resolvability[SampledSeries[Point3Value]]:
        return decide_signal_map(self.source, lambda p: Point3Value(coord=p.point, frame=WORLD_FRAME), POINT3_BLEND)

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        return self.source._sampled_planes(onto)[0]  # the (T, 3) representative-point stack


@dataclass(frozen=True, eq=False)
class _PlaneSignedDistanceSignal(ScalarSignal):
    plane: PlaneSignal
    point: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(
            self.plane, self.point, lambda t: self.plane.at(t).signed_distance(self.point.at(t)), SCALAR_BLEND
        )

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        points, normals = self.plane._sampled_planes(onto)  # (T, 3), (T, 3)
        query = self.point.resolve_over(onto)  # (T, 3)
        signed: np.ndarray = np.einsum("tc,tc->t", query - points, normals)  # n · (q − p₀), per instant
        return signed
