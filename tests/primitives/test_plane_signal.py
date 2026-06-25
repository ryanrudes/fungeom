"""PlaneSignal — a moving oriented plane (the over-time companion to the patch work)."""

from __future__ import annotations

import numpy as np

from fungeom import PlaneSignal, Point3BundleSignal, Point3Signal, Unresolvable
from fungeom.values import IntervalValue, PlaneValue, SampledSeries


def test_direct_construction_and_interpolation() -> None:
    rising = PlaneSignal.from_samples(
        [0.0, 2.0],
        [PlaneValue(point=[0, 0, 0], normal=[0, 0, 1]), PlaneValue(point=[0, 0, 2], normal=[0, 0, 1])],
    )
    assert isinstance(rising.resolve(), SampledSeries)
    assert rising.over().resolve() == IntervalValue(0.0, 2.0)
    assert np.isclose(rising.at(1.0).resolve().point[2], 1.0)  # the point lerps
    assert np.allclose(rising.at(1.0).resolve().normal, [0, 0, 1])


def test_fit_plane_tracks_a_moving_cloud() -> None:
    # a flat square patch that rises from z=0 to z=1 over [0, 2]
    flat0 = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [2, 2, 0]]
    flat1 = [[0, 0, 1], [2, 0, 1], [0, 2, 1], [2, 2, 1]]
    cloud = Point3BundleSignal.from_frames([0.0, 2.0], [flat0, flat1], keys=["a", "b", "c", "d"])
    plane = cloud.fit_plane()
    assert isinstance(plane, PlaneSignal)
    assert np.allclose(np.abs(plane.at(0.0).resolve().normal), [0, 0, 1])  # the patch normal
    assert np.isclose(plane.at(0.0).resolve().point[2], 0.0)  # centroid height
    assert np.isclose(plane.at(2.0).resolve().point[2], 1.0)
    assert np.isclose(plane.at(1.0).resolve().point[2], 0.5)  # interpolated mid-rise


def test_normal_origin_and_signed_distance_readback() -> None:
    flat0 = [[0, 0, 0], [2, 0, 0], [0, 2, 0]]
    flat1 = [[0, 0, 1], [2, 0, 1], [0, 2, 1]]
    plane = Point3BundleSignal.from_frames([0.0, 2.0], [flat0, flat1]).fit_plane()
    assert np.allclose(np.abs(plane.normal().at(1.0).resolve().vector), [0, 0, 1])
    assert np.isclose(plane.origin().at(2.0).resolve().coord[2], 1.0)
    # a point fixed at height 5: clearance to the rising plane is 5 then 4
    point = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])
    sd = plane.signed_distance(point)
    assert np.isclose(abs(sd.at(0.0).resolve()), 5.0)
    assert np.isclose(abs(sd.at(2.0).resolve()), 4.0)


def test_fit_plane_orients_normals_consistently() -> None:
    # two frames whose raw SVD normals could disagree in sign; fit_plane flips to agree,
    # so the midpoint blend is well-posed (would be Unresolvable if they were opposed)
    a = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0.01]]
    b = [[0, 0, 0.5], [1, 0, 0.5], [0, 1, 0.5], [1, 1, 0.51]]
    plane = Point3BundleSignal.from_frames([0.0, 2.0], [a, b]).fit_plane()
    assert isinstance(plane.at(1.0).resolve(), PlaneValue)  # resolves → normals agree


def test_opposed_normals_blend_is_unresolvable() -> None:
    opposed = PlaneSignal.from_samples(
        [0.0, 2.0],
        [PlaneValue(point=[0, 0, 0], normal=[0, 0, 1]), PlaneValue(point=[0, 0, 0], normal=[0, 0, -1])],
    )
    assert isinstance(opposed.at(0.0).resolve(), PlaneValue)  # exact samples are fine
    decision = opposed.at(1.0).decide()
    assert isinstance(decision, Unresolvable)
    assert "opposed normals" in decision.reason


def test_fit_plane_degenerate_frame_is_unresolvable() -> None:
    collinear = [[0, 0, 0], [1, 0, 0], [2, 0, 0]]
    cloud = Point3BundleSignal.from_frames([0.0, 1.0], [collinear, collinear])
    decision = cloud.fit_plane().decide()
    assert isinstance(decision, Unresolvable)
    assert "plane fit failed" in decision.reason


def test_tilting_normal_slerps() -> None:
    tilt = PlaneSignal.from_samples(
        [0.0, 2.0],
        [PlaneValue(point=[0, 0, 0], normal=[0, 0, 1]), PlaneValue(point=[0, 0, 0], normal=[1, 0, 1])],
    )
    mid = tilt.at(1.0).resolve().normal  # slerp between +z and the (1,0,1) tilt
    assert np.isclose(np.linalg.norm(mid), 1.0)  # stays unit
    assert mid[0] > 0 and mid[2] > 0  # genuinely between the two


def test_orient_plane_track_flips_opposed_normals() -> None:
    from fungeom.primitives.bundle.resolvers.fit import orient_plane_track

    track = orient_plane_track(
        [PlaneValue(point=[0, 0, 0], normal=[0, 0, 1]), PlaneValue(point=[0, 0, 0], normal=[0, 0, -1])]
    )
    assert np.allclose(track[1].normal, [0, 0, 1])  # the opposed normal is flipped to agree


def test_inherited_time_ops() -> None:
    from fungeom import Instant, Interval, Sampling, TimeMap, TimeWarp

    rising = PlaneSignal.from_samples(
        [0.0, 2.0],
        [PlaneValue(point=[0, 0, 0], normal=[0, 0, 1]), PlaneValue(point=[0, 0, 2], normal=[0, 0, 1])],
    )
    assert rising.shift(5.0).over().resolve() == IntervalValue(5.0, 7.0)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 5)
    assert np.isclose(rising.resample(grid).at(1.0).resolve().point[2], 1.0)
    clipped = rising.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    assert isinstance(rising.reparameterize(TimeMap.identity()).at(1.0).resolve(), PlaneValue)  # affine path
    assert rising.reparameterize(TimeWarp.through([(0.0, 0.0), (2.0, 4.0)])).over().resolve() == IntervalValue(0.0, 4.0)
