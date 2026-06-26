"""TransformBundleSignal — a pose-set over time (Signal[Bundle[Transform]] by composition)."""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom import (
    Instant,
    Interval,
    Sampling,
    Scalar,
    TimeWarp,
    Transform,
    TransformBundle,
    TransformBundleSignal,
    Unresolvable,
    Vec3,
)
from fungeom.values import IntervalValue, RigidTransform, SampledSeries


def _z(deg: float, tx: float = 0.0) -> Transform:
    """A pose: a rotation of ``deg`` about +z, translated ``tx`` along +x."""
    return Transform.known(RigidTransform.from_rotation(Rotation.from_euler("z", deg, degrees=True), [tx, 0.0, 0.0]))


def _angle(pose: RigidTransform) -> float:
    return float(Rotation.from_matrix(pose.rotation).as_euler("zyx", degrees=True)[0])


def _clip() -> TransformBundleSignal:
    # J0 rotates 0 -> 90 deg about z over [0, 2]; J1 is fixed at identity
    return TransformBundleSignal.from_frames(
        [0.0, 2.0],
        [[_z(0), _z(0)], [_z(90), _z(0)]],
        keys=["J0", "J1"],
    )


def test_construction_and_at_bridges_to_bundle_algebra() -> None:
    clip = _clip()
    assert isinstance(clip.resolve(), SampledSeries)
    assert clip.over().resolve() == IntervalValue(0.0, 2.0)
    mid = clip.at(1.0)  # a TransformBundle — the static collection algebra is available
    assert isinstance(mid, TransformBundle)
    assert np.isclose(_angle(mid.at("J0").resolve()), 45.0)  # geodesic slerp at the midpoint
    assert mid.count().resolve() == 2.0
    assert np.isclose(_angle(clip.at(2.0).at("J0").resolve()), 90.0)  # exact frame, unblended


def test_translation_lerps_alongside_the_rotation_slerp() -> None:
    sig = TransformBundleSignal.from_frames([0.0, 2.0], [[_z(0, 0.0)], [_z(90, 10.0)]], keys=["J"])
    pose = sig.at(1.0).at("J").resolve()
    assert np.allclose(pose.translation, [5.0, 0.0, 0.0])  # linear in translation
    assert np.isclose(_angle(pose), 45.0)


def test_keyless_positional_keys() -> None:
    sig = TransformBundleSignal.from_frames([0.0, 1.0], [[_z(0), _z(0)], [_z(0), _z(0)]])
    assert sig.at(0.0).present(0).resolve() is True
    assert sig.at(0.0).present(1).resolve() is True
    assert sig.at(0.0).resolve().roster == (0, 1)


def test_occlusion_mask_falls_out_of_the_blend() -> None:
    # J1 present only at frame 0 (occluded at frame 1)
    occ = TransformBundleSignal.from_frames(
        [0.0, 2.0],
        [[_z(0), _z(0)], [_z(90), _z(0)]],
        keys=["J0", "J1"],
        present=[[True, True], [True, False]],
    )
    assert occ.at(0.0).present("J1").resolve() is True  # present at the exact frame
    assert isinstance(occ.at(2.0).at("J1").decide(), Unresolvable)  # absent at the exact frame
    # interpolating across the dropout leaves J1 absent (only one bracket has it)…
    assert occ.at(1.0).present("J1").resolve() is False
    # …but J0, present in both brackets, still interpolates
    assert np.isclose(_angle(occ.at(1.0).at("J0").resolve()), 45.0)
    assert occ.at(1.0).count().resolve() == 1.0
    # the interpolated pose-set keeps the full DECLARED roster (J1 absent, not unknown)
    assert occ.at(1.0).resolve().roster == ("J0", "J1")


def test_antipodal_blend_is_strict_over_op_failure() -> None:
    # The one way the partial SE(3) blend differs from the total Point3 lerp: an opposed
    # orientation has no unique geodesic, and one such joint makes the WHOLE interpolated
    # pose-set Unresolvable — an op-failure is never silently turned into absence.
    anti = TransformBundleSignal.from_frames(
        [0.0, 2.0],
        [[_z(0), _z(0)], [_z(180), _z(0)]],  # J0 flips a half-turn; J1 is fine
        keys=["J0", "J1"],
    )
    decision = anti.at(1.0).decide()
    assert isinstance(decision, Unresolvable)
    assert "opposed orientations" in decision.reason
    # but an exact sample never routes through the blend, so it resolves fine
    assert np.isclose(_angle(anti.at(2.0).at("J0").resolve()), 180.0)
    assert anti.at(2.0).count().resolve() == 2.0


def test_exact_interior_sample_bypasses_the_partial_blend() -> None:
    # The crux of "exact samples are never blended": an *interior* exact frame must resolve
    # even when it brackets an antipodal pair — it short-circuits to that frame rather than
    # interpolating. (The boundary case above can't reach this path; only an interior frame
    # of a >=3-frame clip does.) J0: -90 -> +90 (opposed, 180 deg apart) -> +135 about z.
    clip = TransformBundleSignal.from_frames(
        [0.0, 1.0, 2.0],
        [[_z(-90)], [_z(90)], [_z(135)]],
        keys=["J0"],
    )
    # the interior EXACT frame resolves to that frame's pose, despite the antipodal -90->90 bracket
    assert np.isclose(_angle(clip.at(1.0).at("J0").resolve()), 90.0)
    # but interpolating across the opposed bracket is Unresolvable
    interp = clip.at(0.5).decide()
    assert isinstance(interp, Unresolvable)
    assert "opposed orientations" in interp.reason
    # the clean later bracket (90->135) still interpolates
    assert np.isclose(_angle(clip.at(1.5).at("J0").resolve()), 112.5)


def test_inherited_time_ops() -> None:
    clip = _clip()
    assert clip.shift(5.0).over().resolve() == IntervalValue(5.0, 7.0)
    clipped = clip.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    assert np.isclose(_angle(clip.resample(grid).at(1.0).at("J0").resolve()), 45.0)
    # reparameterize by a monotonic warp (the TimeWarp branch)
    warped = clip.reparameterize(TimeWarp.through([(0.0, 0.0), (2.0, 4.0)]))
    assert warped.over().resolve() == IntervalValue(0.0, 4.0)


def test_partiality() -> None:
    clip = _clip()
    # off-domain sample
    assert isinstance(clip.at(9.0).decide(), Unresolvable)
    # frame / time count mismatch (3 frames, 2 times)
    mismatch = TransformBundleSignal.from_frames([0.0, 1.0], [[_z(0)], [_z(0)], [_z(0)]])
    decision = mismatch.decide()
    assert isinstance(decision, Unresolvable)
    assert "3 frames for 2 sample times" in decision.reason
    # per-frame width mismatch (a frame with the wrong number of poses)
    ragged = TransformBundleSignal.from_frames([0.0, 1.0], [[_z(0), _z(0)], [_z(0)]], keys=["J0", "J1"])
    ragged_decision = ragged.decide()
    assert isinstance(ragged_decision, Unresolvable)
    assert "1 poses for 2 keys" in ragged_decision.reason
    # an unresolvable member (a degenerate zero-axis rotation) fails the whole signal — strict build
    degenerate = Transform.rotation(Vec3.of(0, 0, 0), Scalar.of(1))
    bad_member = TransformBundleSignal.from_frames([0.0, 1.0], [[degenerate], [_z(0)]], keys=["J"])
    assert isinstance(bad_member.decide(), Unresolvable)
    # a bad time base (non-increasing) propagates
    bad_times = TransformBundleSignal.from_frames([1.0, 0.0], [[_z(0)], [_z(0)]], keys=["J"])
    assert isinstance(bad_times.decide(), Unresolvable)
    # an empty signal is Unresolvable (no time base) — exercises the keyless empty-grid path
    assert isinstance(TransformBundleSignal.from_frames([], []).decide(), Unresolvable)


def test_at_a_temporal_gap_is_unresolvable() -> None:
    # a max_gap dropout: querying inside the temporal hole is Unresolvable (no invented pose)
    gapped = TransformBundleSignal.from_frames(
        [0.0, 1.0, 5.0, 6.0],
        [[_z(0)], [_z(10)], [_z(50)], [_z(60)]],
        keys=["J"],
        max_gap=2.0,
    )
    assert gapped.support().resolve().intervals == (IntervalValue(0.0, 1.0), IntervalValue(5.0, 6.0))
    assert isinstance(gapped.at(3.0).decide(), Unresolvable)  # inside the gap
    assert np.isclose(_angle(gapped.at(5.5).at("J").resolve()), 55.0)  # interpolates inside the later span


def test_key_projection_matches_at() -> None:
    # The entity-axis slice key(j) pulls one joint's pose trajectory; the commuting square holds
    # under linear interpolation (at(t).at(j) == key(j).at(t)), both Unresolvable together at antipodes.
    clip = _clip()
    assert np.isclose(_angle(clip.key("J0").at(1.0).resolve()), 45.0)
    assert np.allclose(clip.at(1.0).at("J0").resolve().rotation, clip.key("J0").at(1.0).resolve().rotation)
