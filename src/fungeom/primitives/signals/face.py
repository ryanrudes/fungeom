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

That is the *rigid* kind. The other kind is the **per-frame** patch, for a surface that genuinely
deforms: ``Point3BundleSignal.hull_in(plane)`` re-hulls a moving cloud in a moving plane's chart at
every frame, and ``fit_convex_face()`` is that with the plane fitted from the very same points. They
have no static face to transport, so ``region()`` is ``Unresolvable`` for them and the batched
readbacks below fall back to the generic per-instant path.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import overload

import numpy as np

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.face.decidability import FaceDecision
from fungeom.primitives.face.resolvers.base import Face
from fungeom.primitives.face.value import FaceValue
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.instant.resolvers.base import Instant
from fungeom.primitives.plane.value import PlaneValue
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.region2.decidability import Region2Decision
from fungeom.primitives.region2.resolvers.base import Region2
from fungeom.primitives.region2.resolvers.hull import TolerantBundleHullRegion2
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.transform.value import RigidTransform
from fungeom.primitives.signals.bundle import (
    POINT3_BUNDLE_BLEND,
    Point3BundleSignal,
    ScalarBundleSignal,
    decide_lifted_block,
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


class FaceSignal(Signal[FaceValue]):
    """A deferred *moving patch* — a bounded surface whose world geometry varies over time.

    Two kinds, and the difference matters:

    - :meth:`of` — a **rigid** patch: one static ``Face`` transported by a ``TransformSignal``. The
      footprint never changes, only where it sits, so :meth:`region` is a single static region and
      the readbacks below take a fast batched path.
    - :meth:`~fungeom.Point3BundleSignal.hull_in` and
      :meth:`~fungeom.Point3BundleSignal.fit_convex_face` — a **per-frame** patch: the footprint is
      re-hulled at every frame (and, for ``fit_convex_face``, the plane refitted with it). Use these
      when the surface itself deforms, where a rigid transport would be a lie. :meth:`region` is
      ``Unresolvable`` for them and the readbacks take the generic per-instant path.

    Query world geometry as signals: :meth:`plane` (→ ``PlaneSignal``, so ``normal``/``origin``
    follow), :meth:`frame` (→ ``TransformSignal``), :meth:`boundary` (→ ``Point3BundleSignal``),
    :meth:`clearance` (→ ``ScalarSignal`` / ``ScalarBundleSignal``), :meth:`contains`
    (→ ``BoolSignal``). ``at(t)`` gives the patch at one instant. Partiality flows from the source
    and the query point.
    """

    type Value = SampledSeries[FaceValue]
    """The resolved value type — a ``SampledSeries`` of ``FaceValue``s."""

    @classmethod
    def of(cls, face: Face, pose: TransformSignal) -> FaceSignal:
        """A moving patch: the static ``face`` fixed in the frame that moves with ``pose``."""
        return _TransportedFaceSignal(face=face, pose=pose)

    def at(self, instant: Instant | float) -> Face:
        """The transported patch at ``instant`` (→ ``Face``; Unresolvable off-support or in a gap)."""
        from fungeom.primitives.instant.resolvers.literal import as_instant_resolver

        return _FaceSignalAt(signal=self, instant=as_instant_resolver(instant))

    def region(self) -> Region2:
        """The patch's *static* footprint in the plane's chart, when it has one.

        A rigidly transported patch does: transport moves the plane, never the region. A
        **per-frame** patch does not — its footprint is re-hulled per frame — so this decides
        ``Unresolvable`` there rather than returning one frame's hull as though it stood for all of
        them. Ask ``at(t).region()`` for the footprint at an instant.
        """
        return _NoStaticRegion2(signal=self)

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
class _NoStaticRegion2(Region2):
    """The footprint of a patch that has no single static one — a per-frame patch."""

    signal: FaceSignal

    def _decide(self) -> Region2Decision:
        if isinstance(self.signal, _TransportedFaceSignal):
            return self.signal.face.region().decide()
        return Unresolvable(
            "a per-frame patch has no static region — its footprint is refitted every frame; "
            "ask at(t).region() for one instant's"
        )


@dataclass(frozen=True, eq=False)
class _TransportedFaceSignal(FaceSignal):
    """A static patch carried by a moving pose — the rigid case, and the fast one."""

    face: Face
    pose: TransformSignal

    def _decide(self) -> Resolvability[SampledSeries[FaceValue]]:
        decided = self.face.decide()
        if isinstance(decided, Unresolvable):
            return decided
        static_face = decided.value
        return decide_signal_map(self.pose, lambda t: static_face.transformed_by(t), FACE_BLEND)


@dataclass(frozen=True, eq=False)
class _HulledFaceSignal(FaceSignal):
    """A patch re-hulled every frame: *this* cloud's convex hull taken in *that* plane's chart.

    The deforming counterpart of :class:`_TransportedFaceSignal`, and the general form of the
    per-frame fit — the plane is supplied from outside rather than fitted from the same points, so
    the cloud that says *where the surface is* and the cloud that says *how far it extends* need not
    be the same one. ``Point3BundleSignal.fit_convex_face`` is this with the plane fitted from the
    hulled cloud itself.

    Built by composition, per aligned instant: ``Face.on(plane.at(t), hull(cloud.at(t) in that
    chart))``. So it is time-aligned like every other two-signal op (the union of sample instants,
    clipped to the intersection of supports) and every partiality — an unresolvable plane or cloud,
    a frame with fewer than three present points, a projection that is collinear within
    ``tolerance`` — flows out of the composed resolvers rather than being re-implemented here.

    Nothing here orients the normal track. That is deliberate: the plane is the caller's, and so is
    its orientation. ``fit_plane`` already flips each frame's arbitrary SVD normal to agree with the
    previous one before handing the track over, which is why ``fit_convex_face`` still gets a
    continuous chart; a plane signal built some other way keeps whatever orientation it was given.

    **Between samples the footprint is the earlier bracket's**, on an interpolated plane — the
    existing face blend. Interpolating footprints is not well defined: a convex hull's vertex count
    changes from frame to frame, so there is no correspondence to interpolate along. Values *at*
    sample instants are exact, which is what a baked take is read at.
    """

    cloud: Point3BundleSignal
    carrier: PlaneSignal
    tolerance: float

    def _decide(self) -> Resolvability[SampledSeries[FaceValue]]:
        def patch_at(t: float) -> Face:
            plane = self.carrier.at(t)  # bound once: two `at` calls would be two unmemoized nodes
            chart = self.cloud.at(t).in_frame(plane)
            return Face.on(plane, TolerantBundleHullRegion2(cloud=chart, tolerance=self.tolerance))

        return decide_lifted(self.cloud, self.carrier, patch_at, FACE_BLEND)


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

    def _sampled_planes(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        if not isinstance(self.source, _TransportedFaceSignal):
            # A per-frame patch has no static face to batch against; take the generic path.
            return super()._sampled_planes(onto)
        static = self.source.face.plane().resolve()  # PlaneValue; raises if the plane is ungrounded
        poses = self.source.pose.resolve_over(onto)  # (T, 4, 4) — one batched read; raises off-support
        rotation, translation = poses[:, :3, :3], poses[:, :3, 3]
        points = np.einsum("tij,j->ti", rotation, static.point) + translation  # R·p₀ + t
        normals = np.einsum("tij,j->ti", rotation, static.normal)  # R·n (rigid: stays unit)
        return points, normals


def _transport_cloud(cloud: BundleValue[Point3Value], transform: RigidTransform) -> BundleValue[Point3Value]:
    """Move every member of a point cloud rigidly by ``transform`` (world-anchored)."""
    members: dict[Hashable, Point3Value] = {
        key: Point3Value(coord=transform.apply_point(value.coord), frame=WORLD_FRAME)
        for key, value in cloud.members.items()
    }
    return BundleValue(roster=cloud.roster, members=members)


@dataclass(frozen=True, eq=False)
class _FaceSignalFrame(TransformSignal):
    """The patch's canonical frame over time = the moving pose applied to the *static* patch frame.

    Transport (``pose ∘ static_frame``), not a re-gauge of the moving plane — so the frame rotates
    with the pose. Unresolvable for an empty region (no static frame).
    """

    source: FaceSignal

    def _decide(self) -> Resolvability[SampledSeries[RigidTransform]]:
        if not isinstance(self.source, _TransportedFaceSignal):
            # A per-frame patch has a different frame each instant; read it per instant. A
            # resolvable hulled face always has a proper region, so its canonical frame exists.
            return decide_signal_map(self.source, lambda face: face.frame(), TRANSFORM_BLEND)
        decided = self.source.face.frame().decide()  # the static patch frame (Unresolvable if empty)
        if isinstance(decided, Unresolvable):
            return decided
        static_frame = decided.value
        return decide_signal_map(self.source.pose, lambda pose: pose.compose(static_frame), TRANSFORM_BLEND)

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        if not isinstance(self.source, _TransportedFaceSignal):
            # A per-frame patch has no static face to batch against; take the generic path.
            return super().resolve_over(onto)
        static_frame = self.source.face.frame().resolve().matrix  # (4, 4); raises if empty / ungrounded
        poses = self.source.pose.resolve_over(onto)  # (T, 4, 4); raises off-support — one batched read
        return poses @ static_frame  # (T, 4, 4) — compose the whole pose stack with the static frame


@dataclass(frozen=True, eq=False)
class _FaceSignalBoundary(Point3BundleSignal):
    """The footprint vertices in world over time = the static vertices transported by the moving pose."""

    source: FaceSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        if not isinstance(self.source, _TransportedFaceSignal):
            # A per-frame patch's footprint is re-hulled per frame, so its vertices are too — and
            # their count may change between frames, so they cannot be blended, only sampled.
            return decide_signal_map(self.source, lambda face: face.boundary_cloud(), POINT3_BUNDLE_BLEND)
        decided = self.source.face.boundary().decide()  # the static footprint vertices (world)
        if isinstance(decided, Unresolvable):
            return decided
        static_cloud = decided.value
        return decide_signal_map(
            self.source.pose, lambda pose: _transport_cloud(static_cloud, pose), POINT3_BUNDLE_BLEND
        )

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        if not isinstance(self.source, _TransportedFaceSignal):
            # A per-frame patch has no static face to batch against; take the generic path.
            return super().resolve_over(onto)
        cloud = self.source.face.boundary().resolve()  # BundleValue[Point3Value]; raises if ungrounded
        vertices = np.array([cloud.members[key].coord for key in cloud.roster], dtype=float).reshape(-1, 3)
        poses = self.source.pose.resolve_over(onto)  # (T, 4, 4)
        homogeneous = np.concatenate([vertices, np.ones((vertices.shape[0], 1))], axis=1)  # (K, 4)
        values = np.einsum("tij,kj->tki", poses, homogeneous)[..., :3]  # (T, K, 3) — one batched transport
        mask = np.ones((poses.shape[0], vertices.shape[0]), dtype=bool)  # boundary vertices are always present
        return values, mask


def _faces_over(face_signal: FaceSignal, onto: Sampling) -> list[FaceValue]:
    """The patch as carried to each of ``onto``'s instants — the readback's per-frame carrier.

    Reads the decided patch track at the target instants (raising off-support, the eager readback
    contract). Works for any patch track, transported or re-hulled per frame, so the batched
    readbacks below need no special case for either.
    """
    series = face_signal.resolve()
    return [series.sample(float(t)).unwrap() for t in onto.resolve().times]


def _face_clearance_block(face: FaceValue, points: np.ndarray) -> Resolvability[np.ndarray]:
    """One frame's bounded clearance from a ``(N, 3)`` point block to ``face`` — Unresolvable if empty.

    The frame-at-a-time kernel every clearance path goes through, per-instant and batched alike.
    It transports nothing: the patch has *already* been carried to this instant, and the whole
    block is charted, footprint-tested and clamped against it in three numpy passes. So it is
    **bit-identical** to ``face.clearance(p)`` per point — the property that lets ``decide()`` and
    ``resolve_over`` be the same computation rather than two algorithms that agree to within a
    rounding error.
    """
    if face.region.is_empty:
        return Unresolvable("the clearance to an empty face is undefined")
    return Resolvable(face.clearance_block(points))


@dataclass(frozen=True, eq=False)
class _FaceClearanceSignal(ScalarSignal):
    """Per-instant clearance from one point trajectory to the moving patch."""

    face_signal: FaceSignal
    point: Point3Signal

    def _decide(self) -> Resolvability[SampledSeries[float]]:
        return decide_lifted(
            self.face_signal, self.point, lambda t: self.face_signal.at(t).clearance(self.point.at(t)), SCALAR_BLEND
        )

    def resolve_over(self, onto: Sampling) -> np.ndarray:
        """Resample onto ``onto`` and resolve to a raw ``(T,)`` clearance array — the vectorized readback.

        Inverse-transports the point trajectory into the static patch's frame and decomposes the
        bounded distance in one batched op. Resolves eagerly (raises off-support, or if the patch is
        empty — no surface to measure to).
        """
        faces = _faces_over(self.face_signal, onto)
        query = self.point.resolve_over(onto)  # (T, 3)
        clearance = np.empty(query.shape[0])
        for index, face in enumerate(faces):
            clearance[index] = _face_clearance_block(face, query[index][None, :]).unwrap()[0]
        return clearance


@dataclass(frozen=True, eq=False)
class _FaceClearanceBundleSignal(ScalarBundleSignal):
    """Per-marker clearance from a moving cloud to the moving patch — the contact-clearance field."""

    face_signal: FaceSignal
    cloud: Point3BundleSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        return decide_lifted_block(self.face_signal, self.cloud, _face_clearance_block)

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """Resample onto ``onto`` and resolve to a dense ``(T, N)`` clearance array + present mask.

        The contact-clearance field, vectorized: the patch is carried to each target instant and
        the whole cloud measured against it in one numpy pass per frame (occluded members stay
        ``nan`` with a ``False`` mask). The same :func:`_face_clearance_block` the per-instant path
        uses, so this readback and ``at(t)`` agree bit for bit. Resolves eagerly (raises
        off-support, or if the patch is empty).
        """
        faces = _faces_over(self.face_signal, onto)
        cloud, mask = self.cloud.resolve_over(onto)  # (T, N, 3), (T, N)
        clearance = np.empty(mask.shape)
        for index, face in enumerate(faces):
            clearance[index] = _face_clearance_block(face, cloud[index]).unwrap()
        return np.where(mask, clearance, np.nan), mask


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
