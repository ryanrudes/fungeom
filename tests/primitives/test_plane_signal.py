"""PlaneSignal — a moving oriented plane (the over-time companion to the patch work)."""

from __future__ import annotations

import numpy as np

from fungeom import PlaneSignal, Point3BundleSignal, Point3Signal, Sampling, Unresolvable
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


def test_vectorized_readback_matches_per_instant_on_a_sampled_plane() -> None:
    # the base _sampled_planes hook: a fitted (non-face) plane's normal/origin/signed_distance
    # resolve_over must equal the per-instant .at() readback at the sample instants.
    flat0 = [[0, 0, 0], [2, 0, 0], [0, 2, 0]]
    flat1 = [[0, 0, 1], [2, 0, 1], [0, 2, 1]]
    plane = Point3BundleSignal.from_frames([0.0, 2.0], [flat0, flat1]).fit_plane()
    grid = Sampling.at_times([0.0, 2.0])
    point = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])
    cloud = Point3BundleSignal.from_frames([0.0, 2.0], [[[0, 0, 5], [1, 1, 5]]] * 2, keys=["x", "y"])

    normals = plane.normal().resolve_over(grid)
    origins = plane.origin().resolve_over(grid)
    sd_point = plane.signed_distance(point).resolve_over(grid)
    sd_cloud, mask = plane.signed_distance(cloud).resolve_over(grid)
    assert mask.all()
    for i, t in enumerate([0.0, 2.0]):
        assert np.allclose(plane.normal().at(t).resolve().vector, normals[i])
        assert np.allclose(plane.origin().at(t).resolve().coord, origins[i])
        assert np.isclose(plane.signed_distance(point).at(t).resolve(), sd_point[i])
        sd = plane.signed_distance(cloud).at(t).resolve()
        assert np.allclose([sd.members[k] for k in sd.roster], sd_cloud[i])


def test_fit_plane_orients_normals_consistently() -> None:
    # two near-identical planar clouds whose *raw* SVD normals come out antipodal (the SVD sign is
    # arbitrary). fit_plane must flip the track to agree, so the midpoint blend is well-posed —
    # WITHOUT the orient step at(1.0) would be an opposed-normals Unresolvable.
    from fungeom.primitives.bundle.resolvers.fit import fit_plane_coords

    a = [
        [0.2616121342493164, 0.2984911434141233, 0.0],
        [0.8142257405942803, 0.0919159421350969, 0.0],
        [0.600100525965654, 0.7285605268117946, 0.0],
        [0.18790107336660344, 0.05514662733306819, 0.0],
        [0.2749693679060381, 0.6574330148755926, 0.0],
    ]
    b = [
        [0.2616121342493164, 0.2984911434141233, 5.6226566278042805e-06],
        [0.8142257405942803, 0.0919159421350969, 1.5006226330533613e-06],
        [0.600100525965654, 0.7285605268117946, 4.326307908047872e-06],
        [0.18790107336660344, 0.05514662733306819, 6.692972985745203e-06],
        [0.2749693679060381, 0.6574330148755926, 4.227846732701278e-06],
    ]
    # premise (self-checking, so this can never silently revert to a tautology): the raw normals
    # really are antipodal, so the orient step is load-bearing for these clouds.
    raw_a = fit_plane_coords(np.array(a), 1e-9).value.normal
    raw_b = fit_plane_coords(np.array(b), 1e-9).value.normal
    assert np.dot(raw_a, raw_b) < -0.9999999  # opposed before orientation
    plane = Point3BundleSignal.from_frames([0.0, 2.0], [a, b]).fit_plane()
    assert isinstance(plane.at(1.0).resolve(), PlaneValue)  # resolves only because fit_plane re-orients


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
    # query at an *asymmetric* fraction (t=0.5 → frac=0.25) where slerp and a naive lerp+normalize
    # (nlerp) genuinely diverge — at frac=0.5 they coincide, so the old midpoint check could not tell
    # them apart. slerp gives [0.19509, 0, 0.98079]; nlerp would give [0.18737, 0, 0.98229].
    quarter = tilt.at(0.5).resolve().normal
    assert np.allclose(quarter, [0.19509032, 0.0, 0.98078528], atol=1e-6)  # the true slerp point
    assert not np.allclose(quarter, [0.18736550, 0.0, 0.98229127], atol=1e-6)  # …distinctly not nlerp


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
