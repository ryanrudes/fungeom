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
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, overload

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom.core.arrays import ArrayLike, dot3
from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.base import kept_keys, narrowed, renamed
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
from fungeom.primitives.point3.value import Point3Value, as_point3_block
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.sampling.resolvers.base import Sampling
from fungeom.primitives.sampling.value import SamplingValue, TimeSeries, as_times
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
    decided_grid,
    aligned_instants,
    dense_grid_brackets,
    dense_grid_readback,
    resolved_grid,
    support_from_times,
)
from fungeom.primitives.signals.plane import PLANE_BLEND, PlaneSignal
from fungeom.primitives.signals.scalar import SCALAR_BLEND, ScalarSignal

if TYPE_CHECKING:  # the signals.face module imports this one, so the edge is annotation-only
    from fungeom.primitives.signals.face import FaceSignal

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


def _world_anchor(frame: CoordinateFrame | Frame) -> Resolvability[RigidTransform]:
    """The frame-to-world transform that every point of a same-framed block shares.

    Exactly the work one ``Point3.at(x, y, z, frame=frame).decide()`` does before it can
    world-anchor a single point — the grounded check and the parent-chain composition — hoisted
    out of the per-point loop, because a ``(T, N, 3)`` stack carries *one* frame, not ``T·N`` of
    them. Both spellings of a frame reduce to the same transform: a deferred :class:`Frame`
    resolves to an already-world-anchored :class:`CoordinateFrame` (as ``FramedPoint3`` reads
    it), a frame *value* is checked for grounding here (as ``LocatedPoint3`` does), and either
    way an ungrounded frame is Unresolvable with the reason a single point would have given.
    """
    if isinstance(frame, Frame):
        decided = frame.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(decided.value.to_world())
    if not frame.is_grounded:
        return Unresolvable(f"frame {frame.name!r} is not grounded to the world")
    return Resolvable(frame.to_world())


def _anchored(block: np.ndarray, anchor: RigidTransform) -> np.ndarray:
    """A ``(T, N, 3)`` stack of local coordinates carried into the world frame, in one pass.

    The batched form of ``RigidTransform.apply_point``, and **bit-identical to it by construction**:
    both are the one :func:`~fungeom.core.arrays.dot3` expression, differing only in what they
    broadcast over. It used to be written as the sum of the rotation's scaled columns and *compared*
    against a per-point path that still went through ``@`` — which agreed only on architectures
    where BLAS's gemv happened to associate the same way, and did not on x86-64. Matching a
    hand-written sum against a BLAS call is a coincidence to be tested for; sharing the expression
    is a property. The fidelity costs ~17 ms on a stack where the per-point path cost 27 s.
    """
    rotation, translation = anchor.matrix[:3, :3], anchor.matrix[:3, 3]
    return dot3(rotation, block[..., None, :]) + translation


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


def decide_where_over_time[V](
    source: Signal[BundleValue[V]],
    keep: tuple[Hashable, ...] | Roster,
    narrow: Callable[[frozenset[Hashable]], Signal[BundleValue[V]] | None] | None = None,
) -> Resolvability[SampledSeries[BundleValue[V]]]:
    """Restrict every sample of a collection-over-time to ``keep`` — the temporal ``where``.

    The entity axis and the time axis are independent, which is the whole reason this is a
    narrowing rather than a rebuild: keys do not move, so the same key set applies at every
    instant, and the time base, the reconstruction kernel and the temporal support all carry
    through untouched. Restricting cannot open a gap — a sample whose keys are all dropped is a
    valid *empty* collection there, not an undefined one.

    ``keep`` is resolved **once**, not per sample, and an unresolvable :class:`Roster` propagates
    rather than being forced early.

    ``narrow`` is the optional **pushdown**: a source that can build its series over a subset of
    its entity axis directly (``_narrowed_to``) returns an equivalent narrowed signal, and this
    decides *that* instead of deciding the whole collection and discarding most of it. The
    fallback — decide in full, then narrow each sample — is what a source that cannot push down
    still gets, and the two agree sample for sample. The pushdown is skipped when the source has
    already been decided: reading a memoized decision beats recomputing a cheaper one.
    """
    decided_keep = kept_keys(keep)
    if isinstance(decided_keep, Unresolvable):
        return decided_keep
    if narrow is not None and source._decided() is None:
        narrowed_source = narrow(decided_keep.value)
        if narrowed_source is not None:
            # Its samples carry only the kept keys already, so there is nothing left to
            # restrict — and nothing was ever paid for the keys `keep` drops.
            return narrowed_source.decide()
    match source.decide():
        case Resolvable(series):
            narrow_all = tuple(narrowed(sample, decided_keep.value) for sample in series.values)
            return Resolvable(replace(series, values=narrow_all))
        case Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_relabeled_over_time[V](
    source: Signal[BundleValue[V]], mapping: RosterMap
) -> Resolvability[SampledSeries[BundleValue[V]]]:
    """Re-key every sample of a collection-over-time — the temporal identity transfer.

    What retargeting *is*, carried across time: a cloud keyed by source-skeleton markers becomes
    one keyed by target-skeleton joints, at every instant, with each value carried over unchanged
    and the occlusion mask transferring intact. A correspondence is time-invariant, so it is
    decided once and applied to each sample.

    **Unresolvable** when the correspondence collapses two declared keys onto one target — the
    same partiality as the static ``relabel``, reported for the first sample that shows it.
    """
    decided_map = mapping.decide()
    if isinstance(decided_map, Unresolvable):
        return decided_map
    match source.decide():
        case Resolvable(series):
            transferred: list[BundleValue[V]] = []
            for sample in series.values:
                renamed_sample = renamed(sample, decided_map.value)
                if renamed_sample is None:
                    return Unresolvable("relabel collapses distinct keys onto the same target")
                transferred.append(renamed_sample)
            return Resolvable(replace(series, values=tuple(transferred)))
        case Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


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

    def where(self, keys: Sequence[Hashable] | Roster) -> Point3BundleSignal:
        """The sub-cloud restricted to ``keys``, at every instant (roster and support narrow).

        The entity-axis counterpart of :meth:`restrict`, which narrows *time*. A selection is a
        set of keys and keys do not move, so one made at any instant applies at all of them —
        which is what lets a marker subset chosen once (a foot's markers, a patch's vertices)
        stay the same subset for the whole take. The time base and reconstruction are untouched.

        ``keys`` may be an explicit sequence or a deferred :class:`~fungeom.Roster`.
        """
        return _WherePoint3BundleSignal(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def _narrowed_to(self, kept: frozenset[Hashable]) -> Point3BundleSignal | None:
        """An equivalent signal carrying **only** ``kept`` on the entity axis — the ``where`` pushdown.

        ``None`` (the default here) means "I cannot narrow myself" — :func:`decide_where_over_time`
        then decides this signal in full and restricts each sample, which is always correct and
        was for a while the only path. A node that *can* narrow returns a signal whose samples
        already carry only ``kept``, so a selection of k of N markers costs k rather than N: the
        stored frame stack narrows by *column*, and a purely temporal wrapper (``restrict`` /
        ``resample`` / ``reparameterize``) narrows by pushing into its own source, because time
        ops do not read keys and so commute with an entity-axis restriction.

        The contract is exact agreement, not approximate: the narrowed signal must decide to
        precisely what narrowing the full decision sample-by-sample would give — *including* its
        partiality. That is why a node declines (returns ``None``) whenever the keys it would drop
        could carry partiality of their own; a dropped key must not be able to turn an
        ``Unresolvable`` into a value.
        """
        return None

    def relabel(self, mapping: RosterMap) -> Point3BundleSignal:
        """Re-key the cloud through ``mapping`` at every instant — the identity transfer over time.

        The temporal form of ``Point3Bundle.relabel``: a trajectory set keyed by *source*
        entities becomes one keyed by *target* entities, unmapped keys dropping and the occlusion
        mask carrying across. Unresolvable if the correspondence collapses two keys onto one.
        """
        return _RelabeledPoint3BundleSignal(source=self, mapping=mapping)

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
        return self._decided_grid(onto).unwrap()

    def _decided_grid(self, onto: Sampling) -> Resolvability[tuple[np.ndarray, np.ndarray]]:
        """:meth:`resolve_over` as a decision — the non-raising readback a ``_decide`` may reuse.

        The single place the dense cloud grid is produced, so the eager public readback and the
        batched lifts below it are the same computation and cannot drift apart. A carrier that
        stores its samples densely overrides this with a vectorized shortcut.
        """
        return decided_grid(self.resample(onto), lambda value: value.coord, np.full(3, np.nan))

    def _sample_index(self) -> Resolvability[tuple[TimeSeries, CoverageValue, tuple[Hashable, ...]]]:
        """*When* this cloud is sampled, *where* it is defined, and *which* keys it declares.

        The index of the field without its contents. A batched lift needs only these three things
        from the cloud it measures — the coordinates come from :meth:`_decided_grid` in one numpy
        pass — yet deciding the cloud to read them off builds a ``Point3Value`` for every point of
        every frame, which on a real take is millions of objects the lift never looks at. A carrier
        that already knows its own time base answers this without materializing anything.

        The default is honest rather than cheap: decide, and read the index off the result. A
        subclass may override *only* if its index is a genuine constant of the carrier. Overriding
        does **not** have to reproduce every partiality the full decide would report — an index is
        not a proof of resolvability, and whatever it omits surfaces from :meth:`_decided_grid`,
        which the lift calls next and which decides through the ordinary path.
        """
        decided = self.decide()
        if isinstance(decided, Unresolvable):
            return decided
        series = decided.value
        return Resolvable((series.times, series.support, series.values[0].roster))

    def fit_plane(self, *, tolerance: float = 1e-6) -> PlaneSignal:
        """The least-squares plane fitted to the cloud at every frame (→ ``PlaneSignal``).

        The **moving patch surface** — a batched per-frame SVD fit (the over-time companion to
        the static ``Point3Bundle.fit_plane``). Consecutive normals are oriented to agree (the
        per-frame SVD sign is arbitrary), so the plane track is continuous and its slerp blend
        well-posed. Strict: a frame whose cloud is degenerate (fewer than three present points,
        near-collinear, or isotropic) makes the whole signal ``Unresolvable``.
        """
        return _FittedPlaneSignal(source=self, tolerance=tolerance)

    def hull_in(self, plane: PlaneSignal, *, tolerance: float = 1e-6) -> FaceSignal:
        """This cloud's **convex** hull, taken in ``plane``'s chart at every frame (→ ``FaceSignal``).

        The bounded patch whose surface is decided *elsewhere*. Per aligned instant: project this
        cloud into that plane's two-dimensional chart, hull it, and return the result as a ``Face``
        bounded on that plane. :meth:`fit_convex_face` is exactly this with the plane fitted from the
        very same points.

        **Why the plane comes from outside.** One vertex set cannot answer both of a patch's
        questions well. *Where is the surface* wants a genuinely planar sample — the flat
        weight-bearing core of a sole — because a curved rim dragged into the fit tilts the plane.
        *How far does it extend* wants to be inclusive — the whole outline, rim included — because a
        footprint that stops at the flat core under-reports contact. Fitting the plane on one
        selection and hulling another is how both get the sample they need, and it is not
        expressible when the two are fused.

        **What that costs when the two are fused, measured.** On a skateboard deck (reported by
        ``retarget_perfect_data``, the first use of this in anger): the plane fitted on the deck's
        49-vertex flat core and bounded by the 91-vertex whole top fits to **1.24 mm rms**, while
        those boundary vertices sit **15.78 mm rms and 38.28 mm worst** off that plane — the
        kicktails, which are real geometry and belong in the footprint. Fit the plane over all 91
        instead, as the fused form must, and it comes out **9.94° off horizontal**: the tails lever
        the surface away from the face the board actually stands on. A patch is then measured
        against a plane tilted ten degrees from the contact it is meant to detect, which is not a
        tolerance problem and cannot be tuned away.

        **Convex is in the name because it is a modeling choice, not a property of the data.** A
        hull is right for a sole or a deck and wrong for a splayed hand, whose true footprint is
        concave; this library will not pick that for you behind a neutral name.

        Time-aligned like every two-signal op: the union of the two signals' sample instants, clipped
        to the intersection of their supports, read linearly between them. ``Unresolvable`` if either
        signal is, if their supports are disjoint, or — strictly, at *any* aligned instant — if the
        cloud has fewer than three present points there or its projection into that instant's chart
        is collinear within ``tolerance``. That last case is what makes ``tolerance`` earn its place
        here: a plane tilted steeply against the cloud projects it to something arbitrarily close to
        a line, whose hull is a sliver of numerical noise rather than a footprint.

        Between samples the footprint is the earlier bracket's, on an interpolated plane — a convex
        hull's vertex count changes frame to frame, so there is no correspondence to interpolate a
        footprint along. Values *at* sample instants are exact.
        """
        from fungeom.primitives.signals.face import _HulledFaceSignal

        return _HulledFaceSignal(cloud=self, carrier=plane, tolerance=tolerance)

    def fit_convex_face(self, *, tolerance: float = 1e-6) -> FaceSignal:
        """The **convex** patch fitted to the cloud at every frame (→ ``FaceSignal``).

        The bounded companion to :meth:`fit_plane`, and precisely
        ``self.hull_in(self.fit_plane(tolerance=t), tolerance=t)`` — per frame, fit the least-squares
        plane to these points, then hull these same points in that plane's chart. Bounded is the
        point: an unbounded plane reports a foot as touching a floor it is two metres to the side of,
        while a patch's ``clearance`` is the honest distance to the *footprint*.

        Use :meth:`hull_in` instead when the plane should be fitted to a *different* selection than
        the one hulled — the usual case for a real surface, where the flat core that locates the
        plane is a subset of the outline that bounds it. Fusing them where they should differ is not
        a small error: on a real skateboard deck it tilts the fitted plane 9.94° off the face the
        board stands on (see :meth:`hull_in`).

        **Convex is in the name because it is a modeling choice, not a property of the data.** A
        hull is right for a sole or a deck and wrong for a splayed hand, whose true footprint is
        concave; this library will not pick that for you behind a neutral name.

        Use it where the surface genuinely deforms. For a patch that only *moves* — one rigidly
        driven by a single bone — ``FaceSignal.of(face, pose)`` fits once and transports, which is
        exact and far cheaper.

        Strict: a frame whose cloud is degenerate (fewer than three present points, near-collinear,
        or isotropic) makes the whole signal ``Unresolvable``.
        """
        return self.hull_in(self.fit_plane(tolerance=tolerance), tolerance=tolerance)

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
                width = len(self.member_keys)
                mask = None if self.present is None else self.present[: base.count, :width]
                # Whether the per-point path would build a single point at all. It is the only
                # thing an ungrounded frame can spoil, so a stack with nothing present resolves
                # to empty clouds however detached its frame is — as it does point by point.
                occupied = base.count > 0 and width > 0 and (mask is None or bool(mask.any()))
                anchor = _world_anchor(self.frame)
                if isinstance(anchor, Unresolvable):
                    if occupied:
                        return anchor
                    empty = [BundleValue[Point3Value](roster=self.member_keys, members={}) for _ in range(base.count)]
                    return Resolvable(self._series(base, empty))
                world = _anchored(self.frames[:, :width, :], anchor.value)  # the whole stack, once
                clouds: list[BundleValue[Point3Value]] = []
                for ti in range(base.count):
                    if mask is None:
                        members = dict(zip(self.member_keys, as_point3_block(world[ti])))
                    else:
                        row = mask[ti]
                        keys = tuple(key for key, ok in zip(self.member_keys, row) if ok)
                        members = dict(zip(keys, as_point3_block(world[ti][row])))
                    clouds.append(BundleValue(roster=self.member_keys, members=members))
                return Resolvable(self._series(base, clouds))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover

    def _series(self, base: SamplingValue, clouds: list[BundleValue[Point3Value]]) -> Point3BundleSignal.Value:
        """This carrier's ``clouds`` over ``base``, with its reconstruction and temporal support."""
        return SampledSeries(
            base.times,
            tuple(clouds),
            self.interpolation,
            self.boundary,
            POINT3_BUNDLE_BLEND,
            support_from_times(base.times, self.max_gap),
        )

    def _narrowed_to(self, kept: frozenset[Hashable]) -> Point3BundleSignal | None:
        """This frame stack with only ``kept``'s **columns** — the leaf of the ``where`` pushdown.

        Sound because a ``(T, N, 3)`` float array has no per-member partiality to lose: the only
        way one of these carriers is Unresolvable is its sampling, its frame-count mismatch, or
        its (single, shared) frame being ungrounded — none of which a column selection can change.
        The one exception is the last: an ungrounded frame bites only when *some* point is built,
        so narrowing to keys that are never present could turn that ``Unresolvable`` into empty
        clouds. This declines in that case and lets the full decide report it, as it does today.
        """
        if isinstance(_world_anchor(self.frame), Unresolvable):
            return None
        columns = [ni for ni, key in enumerate(self.member_keys) if key in kept]
        return replace(
            self,
            frames=self.frames[:, columns, :],
            member_keys=tuple(self.member_keys[ni] for ni in columns),
            present=None if self.present is None else self.present[:, columns],
        )

    def _decided_grid(self, onto: Sampling) -> Resolvability[tuple[np.ndarray, np.ndarray]]:
        """The dense cloud readback, vectorized (the cloud analog of ``TransformSignal.from_matrices``).

        Reads the stored ``(T, N, 3)`` frame stack back in one batched numpy interpolation, skipping
        the per-frame ``Point3`` materialization; falls back to the generic per-instant path for any
        reconstruction the shortcut does not model.

        **The stack is world-anchored first, exactly as :meth:`_decide` anchors it.** A cloud may be
        authored in a non-world ``frame``, and its samples are world-anchored at build; reading the
        raw stored coordinates back would hand out frame-local positions under a world-anchored
        contract — a silently wrong answer wherever the frame is not the identity. Anchoring *before*
        the bracket interpolation (rather than after) is also what keeps this bit-identical to the
        generic path, which lerps values that are already anchored. An ungrounded frame defers to
        that path, which owns the "ungrounded, but nothing present" case.
        """
        anchor = _world_anchor(self.frame)
        if isinstance(anchor, Unresolvable):
            return super()._decided_grid(onto)
        width = len(self.member_keys)
        world = _anchored(self.frames[:, :width, :], anchor.value)
        present = None if self.present is None else self.present[:, :width]
        fast = dense_grid_readback(self.sampling, world, present, self.interpolation, self.boundary, self.max_gap, onto)
        return Resolvable(fast) if fast is not None else super()._decided_grid(onto)

    def _sample_index(self) -> Resolvability[tuple[TimeSeries, CoverageValue, tuple[Hashable, ...]]]:
        """The index straight off the carrier — its own sampling, gap policy and key tuple.

        A dense frame stack *is* its index: the time base is the ``sampling`` it was built with, the
        support is that base under ``max_gap``, and the roster is ``member_keys``. None of the three
        depends on a single coordinate, so none of the ``T·N`` points need building. The frame-count
        check is kept because it decides whether this carrier has a coherent time base at all; the
        one partiality not repeated here — an ungrounded frame — is caught by ``_decided_grid``,
        which defers to the per-instant path and reports it identically.
        """
        match self.sampling.decide():
            case Resolvable(base):
                if self.frames.shape[0] != base.count:
                    return Unresolvable(f"{self.frames.shape[0]} frames for {base.count} sample times")
                return Resolvable((base.times, support_from_times(base.times, self.max_gap), self.member_keys))
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
class _WherePoint3BundleSignal(Point3BundleSignal):
    """The cloud signal ``source`` restricted to the ``keep`` keys at every instant."""

    source: Point3BundleSignal
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_where_over_time(self.source, self.keep, narrow=self.source._narrowed_to)

    def _pushed_down(self) -> Point3BundleSignal | None:
        """The equivalent signal carrying only the kept keys, or ``None`` if the source cannot build one.

        The same pushdown :func:`decide_where_over_time` performs, hoisted so the *readbacks* can
        take it too. Without this a narrowed cloud pays for the whole cloud everywhere except
        ``decide``: its index and its dense grid both fall through to the generic path, which
        materializes the full collection and then discards most of it — measured downstream at
        narrowing to 38% of a cloud buying 3%, while the same cloud built dense ran 2.4× faster.

        Memoized, because narrowing copies the frame stack's kept columns and both readbacks want
        the result. Unlike :func:`decide_where_over_time` this does **not** skip the pushdown when
        the source is already decided: reading a memoized decision beats *re-deciding*, but these
        callers do not want a decision at all — a dense carrier answers its index without touching
        a coordinate, which is cheaper than any series that has already been built.
        """
        # Boxed in a 1-tuple so an absent memo is distinguishable from a computed ``None``
        # (the source declining to narrow), without a sentinel or a cast.
        cached: tuple[Point3BundleSignal | None] | None = getattr(self, "_narrowed_signal", None)
        if cached is None:
            decided_keep = kept_keys(self.keep)
            cached = (None if isinstance(decided_keep, Unresolvable) else self.source._narrowed_to(decided_keep.value),)
            object.__setattr__(self, "_narrowed_signal", cached)
        return cached[0]

    def _sample_index(self) -> Resolvability[tuple[TimeSeries, CoverageValue, tuple[Hashable, ...]]]:
        """The narrowed carrier's index — the kept columns' own, never the whole cloud's."""
        narrowed_signal = self._pushed_down()
        return super()._sample_index() if narrowed_signal is None else narrowed_signal._sample_index()

    def _decided_grid(self, onto: Sampling) -> Resolvability[tuple[np.ndarray, np.ndarray]]:
        """The narrowed carrier's dense readback, so a selection costs the selection."""
        narrowed_signal = self._pushed_down()
        return super()._decided_grid(onto) if narrowed_signal is None else narrowed_signal._decided_grid(onto)


@dataclass(frozen=True, eq=False)
class _RelabeledPoint3BundleSignal(Point3BundleSignal):
    """The cloud signal ``source`` re-keyed through ``mapping`` at every instant."""

    source: Point3BundleSignal
    mapping: RosterMap

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_relabeled_over_time(self.source, self.mapping)


@dataclass(frozen=True, eq=False)
class _ResampledPoint3BundleSignal(Point3BundleSignal):
    source: Point3BundleSignal
    onto: Sampling

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_resampled(self.source, self.onto)

    def _narrowed_to(self, kept: frozenset[Hashable]) -> Point3BundleSignal | None:
        """Narrowed by pushing into the source: re-timing never reads a key, so the two commute."""
        narrowed_source = self.source._narrowed_to(kept)
        return None if narrowed_source is None else replace(self, source=narrowed_source)


@dataclass(frozen=True, eq=False)
class _ReparameterizedPoint3BundleSignal(Point3BundleSignal):
    source: Point3BundleSignal
    by: TimeMap | TimeWarp

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        if isinstance(self.by, TimeWarp):
            return decide_warped(self.source, self.by)
        return decide_reparameterized(self.source, self.by)

    def _narrowed_to(self, kept: frozenset[Hashable]) -> Point3BundleSignal | None:
        """Narrowed by pushing into the source: warping the time base never reads a key, so the two commute."""
        narrowed_source = self.source._narrowed_to(kept)
        return None if narrowed_source is None else replace(self, source=narrowed_source)


@dataclass(frozen=True, eq=False)
class _RestrictedPoint3BundleSignal(Point3BundleSignal):
    source: Point3BundleSignal
    to: Coverage

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[Point3Value]]]:
        return decide_restricted(self.source, self.to)

    def _narrowed_to(self, kept: frozenset[Hashable]) -> Point3BundleSignal | None:
        """Narrowed by pushing into the source: clipping the support never reads a key, so the two commute."""
        narrowed_source = self.source._narrowed_to(kept)
        return None if narrowed_source is None else replace(self, source=narrowed_source)


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

    @classmethod
    def from_matrices(
        cls,
        times: ArrayLike,
        matrices: ArrayLike,
        keys: Sequence[Hashable] | None = None,
        via: Interpolation = Interpolation.linear,
        outside: Boundary = Boundary.undefined,
        max_gap: float | None = None,
        present: ArrayLike | None = None,
    ) -> TransformBundleSignal:
        """A pose-set signal from a dense ``(T, N, 4, 4)`` matrix stack — the vectorized batch carrier.

        The pose-set analog of :meth:`TransformSignal.from_matrices`: it stores the raw ``(T, N, 4, 4)``
        array directly, so there are no ``T·N`` per-frame ``Transform`` wrappers to build and
        :meth:`resolve_over` reads back with one batched per-joint slerp + a numpy translation lerp
        (bypassing the per-object path). ``at`` / ``key`` / lifts still materialize lazily. A ``(T, N)``
        boolean ``present`` mask marks per-frame occlusion exactly as :meth:`from_frames` does.
        """
        data = np.array(matrices, dtype=float)  # copy; expected shape (T, N, 4, 4)
        member_keys = tuple(keys) if keys is not None else tuple(range(data.shape[1]))
        mask = None if present is None else np.array(present, dtype=bool)  # copy
        return _MatrixTransformBundleSignal(
            sampling=Sampling.at_times(times),
            matrices=data,
            member_keys=member_keys,
            present=mask,
            interpolation=via,
            boundary=outside,
            max_gap=max_gap,
        )

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """Resample onto ``onto`` and resolve to a dense ``(T, N, 4, 4)`` array + ``(T, N)`` present mask.

        The pose-set readback: columns follow the roster, an occluded (or off-support-between-brackets)
        joint is ``nan`` with a ``False`` mask. Resolves eagerly (raises if a target is off the support
        or crosses opposed orientations). The :meth:`from_matrices` carrier overrides this with a
        batched fast path; here it is the generic per-instant form.
        """
        return resolved_grid(self.resample(onto), lambda value: value.matrix, np.full((4, 4), np.nan))

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

    def where(self, keys: Sequence[Hashable] | Roster) -> TransformBundleSignal:
        """The sub-set of joints restricted to ``keys``, at every instant.

        The entity-axis counterpart of :meth:`restrict`. Selecting the joints that drive one limb
        is a narrowing of the pose set, not a rebuild of it: the time base, the SE(3) blend and
        the temporal support all carry through unchanged.
        """
        return _WhereTransformBundleSignal(source=self, keep=keys if isinstance(keys, Roster) else tuple(keys))

    def relabel(self, mapping: RosterMap) -> TransformBundleSignal:
        """Re-key the pose set through ``mapping`` at every instant — **what retargeting is**.

        A pose set keyed by *source*-skeleton joints becomes one keyed by *target*-skeleton
        joints, each pose carried across the correspondence unchanged and every unmapped joint
        dropped. Unresolvable if the correspondence is not injective over this roster.
        """
        return _RelabeledTransformBundleSignal(source=self, mapping=mapping)

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


def _batch_quaternion_slerp(q_lo: np.ndarray, q_hi: np.ndarray, frac: np.ndarray) -> np.ndarray:
    """Vectorized shortest-path quaternion slerp — ``(M, N, 4) × (M, N, 4) × (M,) → (M, N, 4)``.

    The batched form of the rotation half of ``TRANSFORM_BLEND`` (the SE(3) geodesic): each joint's
    bracketing quaternions are slerped along the **shorter arc** (the far quaternion is negated when
    their dot is negative), with a plain normalized lerp where the two are near-parallel (avoiding the
    ``sin θ → 0`` singularity). At an exact knot (``frac == 0``, ``q_lo == q_hi``) it returns ``q_lo``.
    Like ``TransformSignal.from_matrices``' fast path, this always takes the short arc rather than
    declining an exactly-antipodal pair, so it agrees with the per-instant blend at every sample
    instant (and between, away from the measure-zero opposed-orientation case).
    """
    dot = np.sum(q_lo * q_hi, axis=-1)  # (M, N)
    q_hi = np.where(dot[..., None] < 0.0, -q_hi, q_hi)
    weight = frac.reshape(-1, 1)  # (M, 1), broadcasts over the joints
    theta = np.arccos(np.clip(np.abs(dot), 0.0, 1.0))  # (M, N) in [0, π/2]
    sin_theta = np.sin(theta)
    near = sin_theta < 1e-9  # near-parallel → plain lerp (the slerp weights are 0/0 there)
    safe = np.where(near, 1.0, sin_theta)
    wa = np.where(near, 1.0 - weight, np.sin((1.0 - weight) * theta) / safe)
    wb = np.where(near, weight, np.sin(weight * theta) / safe)
    blended = wa[..., None] * q_lo + wb[..., None] * q_hi
    unit: np.ndarray = blended / np.linalg.norm(blended, axis=-1, keepdims=True)
    return unit


@dataclass(frozen=True, eq=False)
class _MatrixTransformBundleSignal(TransformBundleSignal):
    """A pose-set signal backed by a dense ``(T, N, 4, 4)`` matrix array — the vectorized batch carrier.

    ``_decide`` materializes ``RigidTransform``s lazily (so ``at`` / ``key`` / lifts work normally),
    but :meth:`resolve_over` reads the raw arrays back with a single batched per-joint quaternion slerp
    + a numpy translation lerp, bypassing the per-frame Python objects entirely.
    """

    sampling: Sampling
    matrices: np.ndarray
    member_keys: tuple[Hashable, ...]
    present: np.ndarray | None
    interpolation: Interpolation
    boundary: Boundary
    max_gap: float | None

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        match self.sampling.decide():
            case Resolvable(base):
                if self.matrices.shape[0] != base.count:
                    return Unresolvable(f"{self.matrices.shape[0]} frames for {base.count} sample times")
                poses: list[BundleValue[RigidTransform]] = []
                for ti in range(base.count):
                    members: dict[Hashable, RigidTransform] = {}
                    for ni, key in enumerate(self.member_keys):
                        if self.present is None or bool(self.present[ti, ni]):
                            members[key] = RigidTransform.from_matrix(self.matrices[ti, ni])
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

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        brackets = dense_grid_brackets(
            self.sampling, self.matrices.shape[0], self.interpolation, self.boundary, self.max_gap, onto
        )
        if brackets is None:
            return super().resolve_over(onto)
        lo, hi, frac = brackets
        count, joints = lo.shape[0], self.matrices.shape[1]
        mask = np.ones((count, joints), dtype=bool) if self.present is None else (self.present[lo] & self.present[hi])
        if bool(np.all(frac == 0.0)):
            # Every target is an exact knot (lo == hi) — the dominant case (resolving onto the track's
            # own grid). Copy the stored matrices straight through, no slerp round-trip: bit-exact and
            # pure-indexing fast.
            out = self.matrices[lo].copy()
        else:
            weight = frac.reshape(-1, 1, 1)  # (M, 1, 1)
            translations = self.matrices[:, :, :3, 3]  # (T, N, 3)
            moved = (1.0 - weight) * translations[lo] + weight * translations[hi]  # (M, N, 3) — lerp
            quaternions = Rotation.from_matrix(self.matrices[:, :, :3, :3].reshape(-1, 3, 3)).as_quat()
            quaternions = quaternions.reshape(self.matrices.shape[0], joints, 4)
            slerped = _batch_quaternion_slerp(quaternions[lo], quaternions[hi], frac)  # (M, N, 4)
            rotated = Rotation.from_quat(slerped.reshape(-1, 4)).as_matrix().reshape(count, joints, 3, 3)
            out = np.zeros((count, joints, 4, 4))
            out[:, :, :3, :3] = rotated
            out[:, :, :3, 3] = moved
            out[:, :, 3, 3] = 1.0
        out = np.where(mask[..., None, None], out, np.nan)
        return out, mask


@dataclass(frozen=True, eq=False)
class _TransformBundleSampleAt(TransformBundle):
    """The pose-set sampled at one instant — bridges back to the static Bundle algebra."""

    signal: TransformBundleSignal
    instant: Instant

    def _decide(self) -> BundleDecision[RigidTransform]:
        return decide_sample(self.signal, self.instant)


@dataclass(frozen=True, eq=False)
class _WhereTransformBundleSignal(TransformBundleSignal):
    """The pose signal ``source`` restricted to the ``keep`` joints at every instant."""

    source: TransformBundleSignal
    keep: tuple[Hashable, ...] | Roster

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        return decide_where_over_time(self.source, self.keep)


@dataclass(frozen=True, eq=False)
class _RelabeledTransformBundleSignal(TransformBundleSignal):
    """The pose signal ``source`` re-keyed through ``mapping`` at every instant."""

    source: TransformBundleSignal
    mapping: RosterMap

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[RigidTransform]]]:
        return decide_relabeled_over_time(self.source, self.mapping)


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


def decide_lifted_block[C](
    carrier: Signal[C],
    cloud: Point3BundleSignal,
    block: Callable[[C, np.ndarray], Resolvability[np.ndarray]],
) -> Resolvability[SampledSeries[BundleValue[float]]]:
    """:func:`decide_lifted` with the *member* axis batched — a cloud measured against a carrier.

    Identical in meaning to lifting ``carrier.at(t) ⊕ cloud.at(t)`` per instant: the same
    :func:`aligned_instants` time base and support, the same per-instant carrier value, the same
    resulting roster and occlusion. What differs is only *how* a frame is computed — the cloud is
    read back as one dense ``(T, N, 3)`` grid and ``block(value, points)`` answers a whole frame's
    members in arrays, instead of building N resolvers per instant. That is the difference between
    a contact field costing one numpy pass per frame and costing ``T·N`` trips through the static
    algebra, and it is why this exists as a separate helper rather than an optimization inside
    :func:`decide_lifted`, which cannot know that a member-wise op batches.

    ``block`` returns ``Unresolvable`` for a frame it cannot answer (an empty patch has no surface
    to measure to), exactly as the per-instant resolver would, so partiality still propagates.
    Occluded members are ``nan`` in the grid and simply omitted from the frame's bundle.
    """
    decided_carrier = carrier.decide()
    if isinstance(decided_carrier, Unresolvable):
        return decided_carrier
    carrier_series = decided_carrier.value
    shape = cloud._sample_index()  # the cloud's when/where/which — no points materialized
    if isinstance(shape, Unresolvable):
        return shape
    cloud_times, cloud_support, roster = shape.value
    aligned = aligned_instants(carrier_series.times, carrier_series.support, cloud_times, cloud_support)
    if isinstance(aligned, Unresolvable):
        return aligned
    times, support = aligned.value
    grid = cloud._decided_grid(Sampling.at_times(times))
    if isinstance(grid, Unresolvable):
        # This is where a cloud that cannot be read at all reports it. The index above is
        # deliberately not a proof of resolvability — a dense carrier answers it from its own
        # sampling without touching a coordinate — so a partiality that only the values expose
        # (an ungrounded frame, say) arrives here, from the same per-instant path that would
        # have raised it, with the same reason.
        return grid
    points, mask = grid.value
    frames: list[BundleValue[float]] = []
    for index, t in enumerate(times):
        sampled = carrier_series.sample(t)
        if isinstance(sampled, Unresolvable):
            return sampled
        row = block(sampled.value, points[index])
        if isinstance(row, Unresolvable):
            return row
        values = row.value
        members = {key: float(values[column]) for column, key in enumerate(roster) if mask[index, column]}
        frames.append(BundleValue(roster=roster, members=members))
    return Resolvable(
        SampledSeries(
            as_times(times), tuple(frames), Interpolation.linear, Boundary.undefined, SCALAR_BUNDLE_BLEND, support
        )
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

    def resolve_over(self, onto: Sampling) -> tuple[np.ndarray, np.ndarray]:
        """Resample onto ``onto`` and resolve to a dense ``(T, N)`` array + ``(T, N)`` present mask.

        The vectorized readback of the contact-clearance field: reads the stored ``(T, N)`` frame
        stack back in one batched numpy interpolation, skipping per-frame materialization; falls back
        to the generic per-instant path for any reconstruction the shortcut does not model.
        """
        fast = dense_grid_readback(
            self.sampling, self.frames, self.present, self.interpolation, self.boundary, self.max_gap, onto
        )
        return fast if fast is not None else super().resolve_over(onto)


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


def _plane_signed_distance_block(plane: PlaneValue, points: np.ndarray) -> Resolvability[np.ndarray]:
    """One frame's signed distances from a ``(N, 3)`` point block to ``plane`` — ``n · (qₖ − p₀)``.

    Bit-identical to :meth:`PlaneValue.signed_distance` per point: a length-3 matrix-vector product
    sums in the same order as the scalar dot it replaces.
    """
    distances: np.ndarray = dot3(plane.normal, points - plane.point)
    return Resolvable(distances)


@dataclass(frozen=True, eq=False)
class _PlaneClearanceBundleSignal(ScalarBundleSignal):
    """Per-marker signed distance from a moving cloud to a moving plane — the clearance field over time."""

    plane: PlaneSignal
    cloud: Point3BundleSignal

    def _decide(self) -> Resolvability[SampledSeries[BundleValue[float]]]:
        return decide_lifted_block(self.plane, self.cloud, _plane_signed_distance_block)

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
