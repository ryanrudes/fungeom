"""``TransformSignal`` — a rigid pose that varies over time (the SE(3) manifold).

The motion-capture workhorse: a full pose (rotation + translation) over time. Its
blend interpolates the rotation by the geodesic on SO(3) (axis-angle slerp) and the
translation linearly. Like a direction, the rotation part is *partial* — opposed
orientations (a half-turn apart) have no unique interpolating geodesic, so
``between`` is :class:`~fungeom.Unresolvable` there. Everything else reuses the
generic core.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom.core.arrays import ArrayLike
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.coverage.resolvers.base import Coverage
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.interval.resolvers.base import Interval
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.scalar import ScalarSignal
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_derivative,
    decide_lifted_n,
    decide_reparameterized,
    decide_resampled,
    decide_restricted,
    decide_sample,
    resolved_rows,
    decide_sampled,
    decide_warped,
)
from fungeom.primitives.signals.vec3 import VEC3_BLEND, Vec3Signal
from fungeom.primitives.timemap.resolvers.base import TimeMap
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.resolvers.base import TimeWarp
from fungeom.primitives.transform.decidability import RigidTransformDecision
from fungeom.primitives.transform.resolvers.base import Transform
from fungeom.primitives.transform.value import RigidTransform
from fungeom.primitives.vec3.value import Float3, as_vec3

_HALF_TURN = np.pi - 1e-9


class _TransformBlend:
    """Geodesic blend on SE(3) — slerp the rotation, lerp the translation."""

    def between(self, a: RigidTransform, b: RigidTransform, frac: float) -> Resolvability[RigidTransform]:
        rot_a = Rotation.from_matrix(a.rotation)
        rotvec = (Rotation.from_matrix(b.rotation) * rot_a.inv()).as_rotvec()
        if float(np.linalg.norm(rotvec)) >= _HALF_TURN:
            return Unresolvable("no unique rotation between opposed orientations")
        rotation = Rotation.from_rotvec(frac * rotvec) * rot_a
        translation = a.translation + frac * (b.translation - a.translation)
        return Resolvable(RigidTransform.from_rotation(rotation, translation))


TRANSFORM_BLEND = _TransformBlend()


class TransformSignal(Signal[RigidTransform]):
    """A deferred rigid-pose-valued function of time, reconstructed on SE(3).

    :meth:`at` returns a rich ``Transform``; ``resolve()`` yields a
    ``SampledSeries[RigidTransform]``. Additionally Unresolvable wherever the
    interpolation would cross opposed orientations.
    """

    type Value = SampledSeries[RigidTransform]
    """The resolved value type — a ``SampledSeries`` of rigid transforms."""

    @classmethod
    def sampled(
        cls,
        sampling: Sampling,
        values: Sequence[RigidTransform],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> TransformSignal:
        """A signal of pose ``values`` over ``sampling``, read ``via`` a kernel.

        Samples spaced more than ``max_gap`` seconds apart are treated as a dropout.
        """
        return _SampledTransformSignal(
            sampling=sampling, values=tuple(values), interpolation=via, boundary=outside, max_gap=max_gap
        )

    @classmethod
    def from_samples(
        cls,
        times: ArrayLike,
        values: Sequence[RigidTransform],
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
    ) -> TransformSignal:
        """A signal sampled at explicit ``times`` (sugar over :meth:`sampled`)."""
        return cls.sampled(Sampling.at_times(times), values, via=via, outside=outside, max_gap=max_gap)

    def at(self, instant: Instant | float) -> Transform:
        """The pose at ``instant`` (Unresolvable off-domain or across opposed orientations)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _TransformSampleAt(signal=self, instant=as_instant_resolver(instant))

    def resample(self, onto: Sampling) -> TransformSignal:
        """This signal reconstructed onto a new time base."""
        return _ResampledTransformSignal(source=self, onto=onto)

    def reparameterize(self, by: AffineTimeMap | TimeMap | TimeWarp) -> TransformSignal:
        """This signal's time base affinely warped ``by`` a map (shift / scale / reverse)."""
        if isinstance(by, TimeWarp):
            return _ReparameterizedTransformSignal(source=self, by=by)
        from fungeom.primitives.timemap.resolvers.literal import as_timemap_resolver

        return _ReparameterizedTransformSignal(source=self, by=as_timemap_resolver(by))

    def restrict(self, to: Interval | Coverage) -> TransformSignal:
        """Narrow this signal's support to its overlap with ``to`` (Unresolvable if disjoint)."""
        window = to if isinstance(to, Coverage) else Coverage.of([to])
        return _RestrictedTransformSignal(source=self, to=window)

    def shift(self, by: Duration | float) -> TransformSignal:
        """This signal translated in time by ``by`` (sugar for ``reparameterize(TimeMap.shift(by))``)."""
        return self.reparameterize(TimeMap.shift(by))

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        """Resample onto ``onto`` and resolve to a raw ``(T, 4, 4) array`` — the vectorized readback.

        The sanctioned exit into numpy; resolves eagerly (raises ``UnresolvableError`` if a
        target is off the support).
        """
        return resolved_rows(self.resample(onto), lambda value: value.matrix)

    @classmethod
    def lift(cls, sources: Sequence[Signal[Any]], combine: Callable[..., Transform]) -> TransformSignal:
        """Build a pose signal by combining ``sources`` per instant (the general escape hatch)."""
        return _LiftedTransformSignal(sources=tuple(sources), combine=combine)

    def map(self, transform: Callable[[Transform], Transform]) -> TransformSignal:
        """Apply ``transform`` to this pose at each instant (→ ``TransformSignal``; the unary lift)."""
        return _LiftedTransformSignal(sources=(self,), combine=transform)

    def angular_velocity(self) -> Vec3Signal:
        """The world-frame angular velocity over time (→ ``Vec3Signal``; rad/s).

        Finite differences of the rotation on SO(3): the relative rotation between bracketing
        samples, mapped to a rotation vector by the closed-form matrix log (Rodrigues), over the
        elapsed time. Exact on the grid; Unresolvable with fewer than two samples. The translation
        is ignored — pair with :meth:`Point3Signal.velocity` for linear motion.
        """
        return _AngularVelocityVec3Signal(source=self)

    def angular_speed(self) -> ScalarSignal:
        """The magnitude of the angular velocity over time — ``angular_velocity().norm()`` (rad/s)."""
        return self.angular_velocity().norm()


@dataclass(frozen=True, eq=False)
class _LiftedTransformSignal(TransformSignal):
    """A pose signal built by combining N sources per instant — the general lift / map."""

    sources: tuple[Signal[Any], ...]
    combine: Callable[..., Transform]

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        return decide_lifted_n(self.sources, lambda t: self.combine(*(s.at(t) for s in self.sources)), TRANSFORM_BLEND)


@dataclass(frozen=True, eq=False)
class _AngularVelocityVec3Signal(Vec3Signal):
    """The world-frame angular velocity of a pose signal — a ``Vec3Signal`` (closed-form SO(3) log)."""

    source: TransformSignal

    def _decide(self) -> Resolvability[SampledSeries[Float3]]:
        def slope(a: RigidTransform, b: RigidTransform, dt: float) -> Float3:
            relative = Rotation.from_matrix(b.rotation) * Rotation.from_matrix(a.rotation).inv()
            return as_vec3(relative.as_rotvec() / dt)

        return decide_derivative(self.source, slope, VEC3_BLEND)


@dataclass(frozen=True, eq=False)
class _SampledTransformSignal(TransformSignal):
    sampling: Sampling
    values: tuple[RigidTransform, ...]
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        return decide_sampled(
            self.sampling, self.values, self.interpolation, self.boundary, TRANSFORM_BLEND, self.max_gap
        )


@dataclass(frozen=True, eq=False)
class _ResampledTransformSignal(TransformSignal):
    source: TransformSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        return decide_resampled(self.source, self.onto)


@dataclass(frozen=True, eq=False)
class _ReparameterizedTransformSignal(TransformSignal):
    source: TransformSignal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)


@dataclass(frozen=True, eq=False)
class _RestrictedTransformSignal(TransformSignal):
    source: TransformSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        return decide_restricted(self.source, self.to)


@dataclass(frozen=True, eq=False)
class _TransformSampleAt(Transform):
    signal: TransformSignal
    instant: Instant

    def _decide(self) -> RigidTransformDecision:
        return decide_sample(self.signal, self.instant)
