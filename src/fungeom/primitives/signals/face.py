"""``FaceSignal`` — a *moving patch*: a static :class:`~fungeom.Face` fixed in a frame that moves
over time (a :class:`~fungeom.TransformSignal`).

A patch is a `Face` (a `Plane` carrying a `Region2`) bolted to a body segment; the segment's pose
over time is a `TransformSignal`, so the patch's *world* geometry varies with it while the
plane-local region stays fixed. ``FaceSignal.of(face, pose)`` is that moving patch. Ask it for its
world geometry as ordinary signals — ``plane`` / ``frame`` / ``boundary`` / ``clearance`` — then
``resolve_over`` those onto a track's timestamps. Partiality flows end to end: a clearance against
an occluded or off-support point is ``Unresolvable``, never a silently-transported NaN.

It is a ``Signal[FaceValue]`` (each instant's transported patch); the per-instant value is the
static face moved by the pose at that instant, blended between samples by interpolating the plane
(lerp point / slerp normal) with the region kept.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import overload

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.face.decidability import FaceDecision
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.face.value import FaceValue
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.signals.bundle import (
    POINT3_BUNDLE_BLEND,
    SCALAR_BUNDLE_BLEND,
    Point3BundleSignal,
    ScalarBundleSignal,
)
from fungeom.primitives.signals.boolean import BoolSignal
from fungeom.primitives.signals.plane import PLANE_BLEND, PlaneSignal
from fungeom.primitives.signals.point3 import Point3Signal
from fungeom.primitives.signals.scalar import SCALAR_BLEND, ScalarSignal
from fungeom.primitives.signals.series import (
    SampledSeries,
    Signal,
    decide_lifted,
    decide_signal_map,
)
from fungeom.primitives.signals.transform import TRANSFORM_BLEND, TransformSignal
from fungeom.primitives.transform.value import RigidTransform


class _FaceBlend:
    """Blend two patches by blending their planes (lerp point / slerp normal); region is kept.

    Partial exactly where the plane blend is — opposed normals between samples are ``Unresolvable``,
    just like a ``Direction3Signal`` / ``PlaneSignal``.
    """

    def between(self, a: FaceValue, b: FaceValue, frac: float) -> Resolvability[FaceValue]:
        blended = PLANE_BLEND.between(a.plane, b.plane, frac)
        if isinstance(blended, Unresolvable):
            return blended
        return Resolvable(FaceValue(plane=blended.value, region=a.region))


FACE_BLEND = _FaceBlend()


@dataclass(frozen=True, eq=False)
class FaceSignal(Signal[FaceValue]):
    """A deferred *moving patch* — a static ``Face`` transported by a ``TransformSignal`` over time.

    Build with :meth:`of`. Query its world geometry as signals: :meth:`plane` (→ ``PlaneSignal``,
    so ``normal``/``origin`` follow), :meth:`frame` (→ ``TransformSignal``), :meth:`boundary`
    (→ ``Point3BundleSignal``), :meth:`clearance` (→ ``ScalarSignal`` / ``ScalarBundleSignal``),
    :meth:`contains` (→ ``BoolSignal``); :meth:`region` is the static (plane-local) ``Region2``.
    ``at(t)`` gives the transported ``Face`` at one instant. Partiality flows from the pose and the
    query point.
    """

    face: Face
    pose: TransformSignal

    type Value = SampledSeries[FaceValue]
    """The resolved value type — a ``SampledSeries`` of transported ``FaceValue``s."""

    @classmethod
    def of(cls, face: Face, pose: TransformSignal) -> FaceSignal:
        """A moving patch: the static ``face`` fixed in the frame that moves with ``pose``."""
        return cls(face=face, pose=pose)

    def _decide(self) -> Resolvability[SampledSeries[FaceValue]]:
        decided = self.face.decide()
        if isinstance(decided, Unresolvable):
            return decided
        static_face = decided.value
        return decide_signal_map(self.pose, lambda t: static_face.transformed_by(t), FACE_BLEND)

    def at(self, instant: Instant | float) -> Face:
        """The transported patch at ``instant`` (→ ``Face``; Unresolvable off-support or in a gap)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _FaceSignalAt(signal=self, instant=as_instant_resolver(instant))

    def region(self) -> Region2:
        """The patch's region — *static*, in the plane's chart (transport does not move it)."""
        return self.face.region()

    def plane(self) -> PlaneSignal:
        """The patch's oriented surface over time (→ ``PlaneSignal``; ``normal`` / ``origin`` follow)."""
        return _FaceSignalPlane(source=self)

    def frame(self) -> TransformSignal:
        """The canonical patch frame over time (→ ``TransformSignal``; Unresolvable if the region is empty)."""
        return _FaceSignalFrame(source=self)

    def boundary(self) -> Point3BundleSignal:
        """The footprint vertices in world over time, keyed ``0..N-1`` (→ ``Point3BundleSignal``)."""
        return _FaceSignalBoundary(source=self)

    @overload
    def clearance(self, point: Point3Signal) -> ScalarSignal: ...
    @overload
    def clearance(self, point: Point3BundleSignal) -> ScalarBundleSignal: ...
    def clearance(self, point: Point3Signal | Point3BundleSignal) -> ScalarSignal | ScalarBundleSignal:
        """The 3-D clearance from ``point`` to the moving patch over time (clamped into the footprint).

        A ``Point3Signal`` gives a ``ScalarSignal``; a ``Point3BundleSignal`` broadcasts to a
        ``ScalarBundleSignal`` (per marker). Time-aligned with the pose; Unresolvable where either
        is, and where the patch is empty.
        """
        if isinstance(point, Point3BundleSignal):
            return _FaceClearanceBundleSignal(face_signal=self, cloud=point)
        return _FaceClearanceSignal(face_signal=self, point=point)

    def contains(self, point: Point3Signal) -> BoolSignal:
        """Whether ``point`` projects into the moving footprint over time (→ ``BoolSignal``).

        The support-polygon membership test lifted to time — the patch's region signed distance to
        the point's in-plane projection, thresholded at ``>= 0`` (boundary included). Undefined
        (Unresolvable) where the pose or point is, keeping occluded membership honest.
        """
        return _FaceFootprintSignedDistance(face_signal=self, point=point).ge(0.0)


@dataclass(frozen=True, eq=False)
class _FaceSignalAt(Face):
    """The transported patch at one instant."""

    signal: FaceSignal
    instant: Instant

    def _decide(self) -> FaceDecision:
        match self.signal.decide(), self.instant.decide():
            case (Resolvable(series), Resolvable(t)):
                sampled = series.sample(float(t))
                if isinstance(sampled, Unresolvable):
                    return sampled
                return Resolvable(sampled.value)
            case (Unresolvable() as bad, _):
                return bad
            case (_, Unresolvable() as bad):
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _FaceSignalPlane(PlaneSignal):
    """The patch's plane over time."""

    source: FaceSignal

    def _decide(self) -> Resolvability[SampledSeries[PlaneValue]]:
        return decide_signal_map(self.source, lambda face: face.plane, PLANE_BLEND)


@dataclass(frozen=True, eq=False)
class _FaceSignalFrame(TransformSignal):
    """The patch's canonical frame over time (Unresolvable for an empty region)."""

    source: FaceSignal

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        decided = self.source.decide()
        if isinstance(decided, Unresolvable):
            return decided
        if decided.value.values and decided.value.values[0].region.is_empty:
            return Unresolvable("an empty face has no frame")
        return decide_signal_map(self.source, lambda face: face.frame(), TRANSFORM_BLEND)


@dataclass(frozen=True, eq=False)
class _FaceSignalBoundary(Point3BundleSignal):
    """The patch's footprint vertices in world over time."""

    source: FaceSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_signal_map(self.source, lambda face: face.boundary_cloud(), POINT3_BUNDLE_BLEND)


@dataclass(frozen=True, eq=False)
class _FaceClearanceSignal(ScalarSignal):
    """Per-instant clearance from one point trajectory to the moving patch."""

    face_signal: FaceSignal
    point: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(
            self.face_signal, self.point, lambda t: self.face_signal.at(t).clearance(self.point.at(t)), SCALAR_BLEND
        )


@dataclass(frozen=True, eq=False)
class _FaceClearanceBundleSignal(ScalarBundleSignal):
    """Per-marker clearance from a moving cloud to the moving patch — the contact-clearance field."""

    face_signal: FaceSignal
    cloud: Point3BundleSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        return decide_lifted(
            self.face_signal,
            self.cloud,
            lambda t: self.face_signal.at(t).clearance(self.cloud.at(t)),
            SCALAR_BUNDLE_BLEND,
        )


@dataclass(frozen=True, eq=False)
class _FaceFootprintSignedDistance(ScalarSignal):
    """The patch region's signed distance (positive inside) to a point's in-plane projection over time."""

    face_signal: FaceSignal
    point: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        def membership(t: float) -> Scalar:
            face = self.face_signal.at(t)
            return face.region().signed_distance(face.plane().to_local(self.point.at(t)))

        return decide_lifted(self.face_signal, self.point, membership, SCALAR_BLEND)
