"""Point3BundleSignal — a point cloud over time (Signal[Bundle[Point3]] by composition)."""

from __future__ import annotations

import numpy as np

from fungeom import (
    CoordinateFrame,
    Instant,
    Interval,
    Point3BundleSignal,
    Sampling,
    Unresolvable,
)
from fungeom.values import IntervalValue, SampledSeries


def _clip() -> Point3BundleSignal:
    # HEAD moves +x over [0, 2]; LWRIST stays put
    return Point3BundleSignal.from_frames(
        [0.0, 2.0],
        [[[0, 0, 0], [5, 0, 0]], [[10, 0, 0], [5, 0, 0]]],
        keys=["HEAD", "LWRIST"],
    )


def test_construction_and_at_bridges_to_bundle_algebra() -> None:
    clip = _clip()
    assert isinstance(clip.resolve(), SampledSeries)
    assert clip.over().resolve() == IntervalValue(0.0, 2.0)
    mid = clip.at(1.0)  # a Point3Bundle — the static collection algebra is available
    assert np.allclose(mid.at("HEAD").resolve().coord, [5, 0, 0])  # interpolated frame
    assert np.allclose(mid.centroid().resolve().coord, [5, 0, 0])
    assert mid.count().resolve() == 2.0
    assert np.allclose(clip.at(2.0).at("HEAD").resolve().coord, [10, 0, 0])  # exact frame


def test_occlusion_mask_falls_out_of_the_blend() -> None:
    # LWRIST is occluded at frame 1 (present only at frame 0)
    occ = Point3BundleSignal.from_frames(
        [0.0, 2.0],
        [[[0, 0, 0], [5, 0, 0]], [[10, 0, 0], [0, 0, 0]]],
        keys=["HEAD", "LWRIST"],
        present=[[True, True], [True, False]],
    )
    assert np.allclose(occ.at(0.0).at("LWRIST").resolve().coord, [5, 0, 0])  # present at frame 0
    assert isinstance(occ.at(2.0).at("LWRIST").decide(), Unresolvable)  # absent at the exact frame
    # interpolating across the dropout leaves LWRIST absent (only one bracket has it)…
    assert isinstance(occ.at(1.0).at("LWRIST").decide(), Unresolvable)
    # …but HEAD, present in both brackets, still interpolates
    assert np.allclose(occ.at(1.0).at("HEAD").resolve().coord, [5, 0, 0])
    assert occ.at(1.0).count().resolve() == 1.0
    # the interpolated cloud keeps the full DECLARED roster (LWRIST is absent, not unknown)
    assert occ.at(1.0).resolve().roster == ("HEAD", "LWRIST")


def test_exact_interior_sample_returns_the_full_frame() -> None:
    # An exact sample must be that frame's cloud — never routed through the support-changing
    # blend. LWRIST is occluded at frame 0 but present at frames 1 and 2; querying the exact
    # interior sample t=1.0 must return it (the commuting square holds at exact samples).
    occ = Point3BundleSignal.from_frames(
        [0.0, 1.0, 2.0],
        [[[0, 0, 0], [9, 9, 9]], [[10, 0, 0], [5, 0, 0]], [[20, 0, 0], [5, 0, 0]]],
        keys=["HEAD", "LWRIST"],
        present=[[True, False], [True, True], [True, True]],
    )
    assert np.allclose(occ.at(1.0).at("LWRIST").resolve().coord, [5, 0, 0])  # exact interior, present
    assert occ.at(1.0).count().resolve() == 2.0
    assert isinstance(occ.at(0.5).at("LWRIST").decide(), Unresolvable)  # but interpolation across the dropout drops it


def test_inherited_time_ops() -> None:
    clip = _clip()
    assert clip.shift(5.0).over().resolve() == IntervalValue(5.0, 7.0)
    clipped = clip.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    assert np.allclose(clip.resample(grid).at(1.0).at("HEAD").resolve().coord, [5, 0, 0])


def test_partiality() -> None:
    clip = _clip()
    # off-domain sample
    assert isinstance(clip.at(9.0).decide(), Unresolvable)
    # frame/time count mismatch (3 frames, 2 times)
    mismatch = Point3BundleSignal.from_frames([0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]], [[2, 0, 0]]])
    decision = mismatch.decide()
    assert isinstance(decision, Unresolvable)
    assert "3 frames for 2 sample times" in decision.reason
    # an ungrounded frame makes the whole signal Unresolvable (build-time grounding)
    detached = Point3BundleSignal.from_frames(
        [0.0, 1.0], [[[0, 0, 0]], [[1, 0, 0]]], frame=CoordinateFrame.detached("loose")
    )
    assert isinstance(detached.decide(), Unresolvable)
