"""FaceSignal — a moving patch: a static Face transported by a pose signal over time."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    Direction3,
    Face,
    FaceSignal,
    Instant,
    Interval,
    Plane,
    PlaneSignal,
    PlaneValue,
    Point3,
    Point3Bundle,
    Point3BundleSignal,
    Point3Signal,
    RigidTransform,
    Region2,
    Sampling,
    TransformSignal,
    Unresolvable,
    UnresolvableError,
)

_FLAT = PlaneValue(point=[0, 0, 0], normal=[0, 0, 1])  # the z = 0 plane, supplied from outside


def _rising_patch() -> FaceSignal:
    # a 4x2 rectangle on the z=0 plane, fixed in a frame that rises z: 0 -> 2 over [0, 2]
    patch = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.rectangle(4, 2))
    pose = TransformSignal.from_samples(
        [0.0, 2.0], [RigidTransform.identity(), RigidTransform.from_translation([0, 0, 2])]
    )
    return FaceSignal.of(patch, pose)


def _grid() -> Sampling:
    return Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 3)  # t = 0, 1, 2


def test_plane_normal_origin_and_frame_over_time() -> None:
    patch = _rising_patch()
    assert np.allclose(patch.plane().origin().resolve_over(_grid())[:, 2], [0, 1, 2])  # rises in z
    assert np.allclose(patch.plane().normal().resolve_over(_grid()), [[0, 0, 1]] * 3)  # normal kept
    assert np.allclose(patch.frame().resolve_over(_grid())[:, 2, 3], [0, 1, 2])  # frame translation rises
    assert np.allclose(patch.frame().at(1.0).resolve().rotation[:, 2], [0, 0, 1])  # +z col = normal
    assert patch.at(1.0).clearance(Point3.at(0, 0, 1)).resolve() == 0.0  # the transported patch is a Face


def test_boundary_is_the_moving_footprint() -> None:
    patch = _rising_patch()
    values, mask = patch.boundary().resolve_over(_grid())
    assert values.shape == (3, 4, 3)  # 3 frames, 4 corners, 3D
    assert mask.all()
    assert np.allclose(values[:, :, 2].T, [[0, 1, 2]] * 4)  # every corner rises with the patch


def test_clearance_point_and_cloud() -> None:
    patch = _rising_patch()
    foot = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])  # fixed 5 up
    assert np.allclose(patch.clearance(foot).resolve_over(_grid()), [5, 4, 3])  # shrinks as the patch rises
    cloud = Point3BundleSignal.from_frames(
        [0.0, 2.0], [[[0, 0, 5], [0.5, 0, 5]], [[0, 0, 5], [0.5, 0, 5]]], keys=["a", "b"]
    )
    values, mask = patch.clearance(cloud).resolve_over(_grid())  # ScalarBundleSignal -> (T, K)
    assert np.allclose(values, [[5, 5], [4, 4], [3, 3]])


def test_contains_footprint_membership_over_time() -> None:
    patch = _rising_patch()
    over = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])  # projects inside the footprint
    beside = Point3Signal.from_samples([0.0, 2.0], [[10, 0, 5], [10, 0, 5]])  # outside it
    assert patch.contains(over).at(1.0).resolve() is True
    assert patch.contains(beside).at(1.0).resolve() is False


def test_partiality_flows_from_pose_point_and_region() -> None:
    patch = _rising_patch()
    # a query off the pose's support -> Unresolvable, not an invented number
    foot = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])
    assert isinstance(patch.clearance(foot).at(9.0).decide(), Unresolvable)
    # an empty patch has no frame
    empty = FaceSignal.of(
        Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty),
        TransformSignal.from_samples([0.0, 2.0], [RigidTransform.identity(), RigidTransform.identity()]),
    )
    assert isinstance(empty.frame().decide(), Unresolvable)


def test_at_off_support_is_unresolvable() -> None:
    patch = _rising_patch()  # pose support is [0, 2]
    assert isinstance(patch.at(9.0).decide(), Unresolvable)  # the transported patch is undefined off-support


def test_blend_across_a_flipped_patch_is_unresolvable() -> None:
    from scipy.spatial.transform import Rotation

    # a pose that flips the patch normal (+z -> -z) between samples: the mid-sample patch blend is
    # antipodal (no unique orientation), so sampling the moving patch there is Unresolvable
    patch = Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.rectangle(2, 2))
    flip = TransformSignal.from_samples(
        [0.0, 2.0],
        [RigidTransform.identity(), RigidTransform.from_rotation(Rotation.from_euler("x", 180, degrees=True))],
    )
    moving = FaceSignal.of(patch, flip)
    assert isinstance(moving.at(1.0).decide(), Unresolvable)  # FACE_BLEND over opposed normals


def test_boundary_and_frame_transport_rotation_in_both_paths() -> None:
    # the fix: a rotating pose must rotate the footprint vertices (R·v + t), not just translate to
    # the moved centroid — and the vectorized readback must agree with the per-instant (_decide) path.
    pts = Point3Bundle.from_map({"a": Point3.at(0, 0, 0), "b": Point3.at(1, 0, 0), "c": Point3.at(0, 1, 0)})
    face = Face.on(pts.fit_plane(), Region2.hull(pts.in_frame(pts.fit_plane())))
    rot = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
    trans = np.array([1.0, 2.0, 3.0])
    m = np.eye(4)
    m[:3, :3] = rot
    m[:3, 3] = trans
    fs = FaceSignal.of(face, TransformSignal.from_matrices(np.array([0.0]), m[None]))
    grid = Sampling.at_times([0.0])

    static_verts = np.array([face.boundary().at(k).resolve().coord for k in range(3)])
    got = fs.boundary().resolve_over(grid)[0][0]  # (K, 3)
    assert np.allclose(np.sort(got, axis=0), np.sort(static_verts @ rot.T + trans, axis=0))  # R·v + t
    # the _decide path (via at) reproduces the vectorized readback
    at_cloud = fs.boundary().at(0.0).resolve()
    assert np.allclose([at_cloud.members[k].coord for k in at_cloud.roster], got)

    # frame transports rigidly: rotation = R · static_frame.R, origin = R · static_origin + t
    static_frame = face.frame().resolve()
    frame = fs.frame().resolve_over(grid)[0]
    assert np.allclose(frame[:3, :3], rot @ static_frame.rotation)
    assert np.allclose(frame[:3, 3], rot @ static_frame.translation + trans)
    assert np.allclose(fs.frame().at(0.0).resolve().matrix, frame)  # _decide path matches


def test_clearance_and_plane_readbacks_match_per_instant_under_rotation() -> None:
    # the vectorized resolve_over of clearance / signed_distance / normal / origin must agree with
    # the per-instant .at() path at the sample instants — including a rotation about the normal,
    # which the footprint must follow (the transformed_by fix; resolve_over inverse-transports it).
    from scipy.spatial.transform import Rotation

    pts = Point3Bundle.from_map(
        {k: Point3.at(*v) for k, v in {"a": (-1, -1, 0), "b": (1, -1, 0), "c": (1, 1, 0), "d": (-1, 1, 0)}.items()}
    )
    face = Face.on(pts.fit_plane().facing(Point3.at(0, 0, 1.0)), Region2.hull(pts.in_frame(pts.fit_plane())))
    m0, m1 = np.eye(4), np.eye(4)
    m1[:3, :3] = Rotation.from_euler("z", 90, degrees=True).as_matrix()  # a 90° spin about the normal
    m1[0, 3] = 1.5  # plus a translation, between the two samples
    fs = FaceSignal.of(face, TransformSignal.from_matrices(np.array([0.0, 1.0]), np.array([m0, m1])))
    grid = Sampling.at_times([0.0, 1.0])
    cloud = Point3BundleSignal.from_frames([0.0, 1.0], [[[1.3, 0.0, 0.4], [0.0, 0.0, 0.2]]] * 2, keys=["edge", "mid"])
    point = Point3Signal.from_samples([0.0, 1.0], [[1.3, 0.0, 0.4]] * 2)

    clear_cloud, mask = fs.clearance(cloud).resolve_over(grid)
    clear_point = fs.clearance(point).resolve_over(grid)
    sd_cloud, _ = fs.plane().signed_distance(cloud).resolve_over(grid)
    sd_point = fs.plane().signed_distance(point).resolve_over(grid)
    normals = fs.plane().normal().resolve_over(grid)
    origins = fs.plane().origin().resolve_over(grid)
    assert mask.all()

    for i, t in enumerate([0.0, 1.0]):
        bundle = fs.clearance(cloud).at(t).resolve()
        assert np.allclose([bundle.members[k] for k in bundle.roster], clear_cloud[i])
        assert np.isclose(fs.clearance(point).at(t).resolve(), clear_point[i])
        sd = fs.plane().signed_distance(cloud).at(t).resolve()
        assert np.allclose([sd.members[k] for k in sd.roster], sd_cloud[i])
        assert np.isclose(fs.plane().signed_distance(point).at(t).resolve(), sd_point[i])
        assert np.allclose(fs.plane().normal().at(t).resolve().vector, normals[i])
        assert np.allclose(fs.plane().origin().at(t).resolve().coord, origins[i])

    # the spin genuinely moved the footprint: the 'edge' marker reads a different bounded clearance
    # at the rotated instant than at the identity one (resolve_over isn't dropping the rotation).
    assert not np.isclose(clear_cloud[0, 0], clear_cloud[1, 0])


def test_clearance_resolve_over_masks_occluded_cloud_members() -> None:
    patch = _rising_patch()  # pose rises z: 0 → 2 over [0, 2]
    cloud = Point3BundleSignal.from_frames(
        [0.0, 2.0],
        [[[0, 0, 5], [0.5, 0, 5]], [[0, 0, 5], [0.5, 0, 5]]],
        keys=["a", "b"],
        present=[[True, True], [True, False]],  # 'b' occluded at t = 2
    )
    values, mask = patch.clearance(cloud).resolve_over(Sampling.at_times([0.0, 2.0]))
    assert mask.tolist() == [[True, True], [True, False]]
    assert np.isnan(values[1, 1])  # the occluded cell is nan with a False mask, like resolved_grid
    assert np.allclose([values[0, 0], values[0, 1], values[1, 0]], [5, 5, 3])  # present cells resolve


def test_clearance_resolve_over_on_an_empty_face_raises() -> None:
    empty = FaceSignal.of(
        Face.on(Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1)), Region2.empty),
        TransformSignal.from_samples([0.0, 2.0], [RigidTransform.identity(), RigidTransform.identity()]),
    )
    grid = Sampling.at_times([0.0, 2.0])
    foot = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 5], [0, 0, 5]])
    cloud = Point3BundleSignal.from_frames([0.0, 2.0], [[[0, 0, 5]], [[0, 0, 5]]], keys=["m"])
    with pytest.raises(UnresolvableError):  # an empty patch has no surface to measure to
        empty.clearance(foot).resolve_over(grid)
    with pytest.raises(UnresolvableError):
        empty.clearance(cloud).resolve_over(grid)


# --- fitted patches: the plane AND the footprint refitted per frame ---------------------------


def _drifting_cloud(frames: int = 4, *, spread: float = 1.0, rise: float = 0.02) -> Point3BundleSignal:
    """A flat, well-spread cloud translating upward — a deforming patch's simplest stand-in."""
    base = np.array([[0.0, 0.0, 0.0], [spread, 0.0, 0.0], [spread, spread, 0.0], [0.0, spread, 0.0]])
    stack = np.stack([base + np.array([0.0, 0.0, rise * step]) for step in range(frames)])
    return Point3BundleSignal.from_frames(np.arange(frames) / 60.0, stack)


def _times(frames: int = 4) -> list[float]:
    return (np.arange(frames) / 60.0).tolist()


def test_fit_convex_face_refits_plane_and_footprint_each_frame() -> None:
    patch = _drifting_cloud().fit_convex_face()
    assert patch.is_resolvable
    first, last = patch.at(0.0).resolve(), patch.at(3 / 60).resolve()
    assert first.region.area() == pytest.approx(1.0)
    assert last.region.area() == pytest.approx(1.0), "a translating patch keeps its footprint"
    assert float(last.plane.point[2]) == pytest.approx(0.06), "but the plane follows the cloud"


def test_a_fitted_patch_has_no_static_region() -> None:
    """Returning one frame's hull as though it stood for all of them would be a lie."""
    decision = _drifting_cloud().fit_convex_face().region().decide()
    assert isinstance(decision, Unresolvable)
    assert "refitted every frame" in decision.reason


def test_a_transported_patch_still_has_its_static_region() -> None:
    """The rigid case is unchanged by the facade split: transport moves the plane, not the region."""
    assert _rising_patch().region().resolve().area() == pytest.approx(8.0), "the 4x2 rectangle"


def test_fitted_patch_answers_the_whole_query_surface() -> None:
    patch = _drifting_cloud().fit_convex_face()
    assert patch.plane().is_resolvable
    assert patch.frame().is_resolvable
    assert len(patch.boundary().at(0.0).resolve().roster) == 4
    above = Point3Signal.from_samples(_times(), [[0.5, 0.5, 1.0]] * 4)
    clearance = patch.clearance(above).resolve_over(Sampling.at_times(_times()))
    assert clearance[0] == pytest.approx(1.0)
    assert clearance[-1] == pytest.approx(0.94), "the patch rises toward the fixed query point"
    assert patch.contains(above).at(0.0).resolve() is True


def test_fitted_patch_readbacks_fall_back_to_the_generic_path() -> None:
    """The batched readbacks key off a *static* face; a fitted patch has none, so they must defer."""
    patch = _drifting_cloud().fit_convex_face()
    onto = Sampling.at_times(_times())
    assert patch.plane().normal().resolve_over(onto).shape == (4, 3)
    assert patch.frame().resolve_over(onto).shape == (4, 4, 4)
    assert patch.boundary().resolve_over(onto)[0].shape == (4, 4, 3)
    cloud = Point3BundleSignal.from_frames(_times(), np.tile([[0.5, 0.5, 1.0]], (4, 1, 1)))
    values, mask = patch.clearance(cloud).resolve_over(onto)
    assert values.shape == (4, 1) and mask.all()


def test_a_degenerate_frame_makes_the_whole_fitted_patch_unresolvable() -> None:
    """Strict, like `fit_plane`: one unusable frame is not quietly dropped."""
    collinear = np.tile(np.array([[0.0, 0, 0], [1.0, 0, 0], [2.0, 0, 0], [3.0, 0, 0]]), (3, 1, 1))
    decision = Point3BundleSignal.from_frames(_times(3), collinear).fit_convex_face().decide()
    assert isinstance(decision, Unresolvable)
    assert "plane fit failed at a frame" in decision.reason


def test_the_footprint_between_samples_is_the_earlier_bracket_s() -> None:
    """A hull's vertex count changes frame to frame, so footprints cannot be interpolated."""
    patch = _drifting_cloud().fit_convex_face()
    midway = patch.at(0.5 / 60).resolve()
    assert midway.region.area() == pytest.approx(patch.at(0.0).resolve().region.area())
    assert float(midway.plane.point[2]) == pytest.approx(0.01), "the plane, though, does interpolate"


# --- hull_in: the footprint of one cloud, on a plane decided somewhere else --------------------


_CORE = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]]  # a flat unit square
_RIM = [3.0, 0.5, 1.0]  # far out and lifted — it belongs to the outline, not to the surface fit


def _core_and_rim(frames: int = 2) -> tuple[Point3BundleSignal, Point3BundleSignal]:
    """The motivating split: a flat core that locates the plane, and a wider outline that bounds it."""
    core = np.stack([np.array(_CORE)] * frames)
    whole = np.stack([np.array([*_CORE, _RIM])] * frames)
    times = _times(frames)
    return Point3BundleSignal.from_frames(times, core), Point3BundleSignal.from_frames(times, whole)


def test_hull_in_fits_the_plane_to_one_selection_and_the_footprint_to_another() -> None:
    """The whole point: the sample that says *where the surface is* need not be the one that bounds it."""
    core, whole = _core_and_rim()
    patch = whole.hull_in(core.fit_plane()).at(0.0).resolve()
    assert abs(float(patch.plane.normal[2])) == pytest.approx(1.0), "the plane is the flat core's"
    assert float(patch.plane.point[2]) == pytest.approx(0.0)
    assert patch.region.area() == pytest.approx(2.0), "the footprint is the whole outline's — square + rim"

    fused = whole.fit_convex_face().at(0.0).resolve()  # what fusing the two questions costs
    assert abs(float(fused.plane.normal[2])) < 0.99, "one cloud for both tilts the plane onto the rim"
    assert float(fused.plane.point[2]) == pytest.approx(0.2)


def test_fit_convex_face_is_exactly_hull_in_its_own_fitted_plane() -> None:
    """Pins the delegation: the fused form *is* the general one with the plane fitted from the same points."""
    cloud = _drifting_cloud()
    fused = cloud.fit_convex_face(tolerance=1e-9).resolve()
    composed = cloud.hull_in(cloud.fit_plane(tolerance=1e-9), tolerance=1e-9).resolve()
    assert np.allclose(np.asarray(fused.times), np.asarray(composed.times))
    for here, there in zip(fused.values, composed.values, strict=True):
        assert np.allclose(here.plane.point, there.plane.point)
        assert np.allclose(here.plane.normal, there.plane.normal)
        assert np.allclose(here.region.rings[0], there.region.rings[0])


def test_hull_in_aligns_the_two_signals_on_the_union_of_their_instants() -> None:
    """A two-signal op, aligned like every other: the cloud's frames and the plane's, together."""
    cloud = _drifting_cloud(3, rise=0.0)  # frames at 0, 1/60, 2/60
    plane = PlaneSignal.from_samples([0.0, 2 / 60], [_FLAT, _FLAT])  # only the two ends
    assert len(cloud.hull_in(plane).resolve().values) == 3, "the union, not the plane's two"


def test_hull_in_answers_the_whole_query_surface_and_has_no_static_region() -> None:
    core, whole = _core_and_rim(3)
    patch = whole.hull_in(core.fit_plane())
    onto = Sampling.at_times(_times(3))
    assert patch.plane().normal().resolve_over(onto).shape == (3, 3)
    assert patch.frame().resolve_over(onto).shape == (3, 4, 4)
    assert patch.boundary().resolve_over(onto)[0].shape == (3, 5, 3), "square + rim, hulled"
    above = Point3Signal.from_samples(_times(3), [[0.5, 0.5, 2.0]] * 3)
    assert patch.clearance(above).resolve_over(onto) == pytest.approx([2.0, 2.0, 2.0])
    decision = patch.region().decide()
    assert isinstance(decision, Unresolvable) and "refitted every frame" in decision.reason


def test_hull_in_refuses_a_frame_with_too_few_present_points() -> None:
    cloud = Point3BundleSignal.from_frames(
        [0.0, 1.0],
        [_CORE[:3]] * 2,
        present=[[True, True, True], [True, True, False]],  # one drops out at t = 1
    )
    decision = cloud.hull_in(PlaneSignal.from_samples([0.0, 1.0], [_FLAT, _FLAT])).decide()
    assert isinstance(decision, Unresolvable)
    assert "needs at least 3 points, got 2" in decision.reason


def test_hull_in_refuses_a_frame_whose_cloud_is_wholly_absent() -> None:
    cloud = Point3BundleSignal.from_frames(
        [0.0, 1.0], [_CORE[:3]] * 2, present=[[True, True, True], [False, False, False]]
    )
    decision = cloud.hull_in(PlaneSignal.from_samples([0.0, 1.0], [_FLAT, _FLAT])).decide()
    assert isinstance(decision, Unresolvable)
    assert "needs at least 3 points, got 0" in decision.reason


def test_hull_in_refuses_a_footprint_that_is_collinear_within_tolerance() -> None:
    """A plane tilted hard against the cloud projects it to a sliver — a hull of numerical noise.

    Discriminating on purpose: the sliver is 1e-9 thick, so it is *not* exactly degenerate and the
    exact (Qhull) test accepts it. Only the tolerance refuses it — and lowering the tolerance below
    the sliver's thickness lets it through again, which is what makes `tolerance` a reified input
    rather than a hidden constant.
    """
    sliver = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1e-9], [0.0, 1.0, 1e-9]]
    cloud = Point3BundleSignal.from_frames([0.0, 1.0], [sliver] * 2)
    edge_on = PlaneSignal.from_samples([0.0, 1.0], [PlaneValue(point=[0, 0, 0], normal=[1, 0, 0])] * 2)
    decision = cloud.hull_in(edge_on).decide()
    assert isinstance(decision, Unresolvable)
    assert "collinear within tolerance" in decision.reason
    assert cloud.hull_in(edge_on, tolerance=1e-12).is_resolvable, "the same points, a stricter tolerance"


def test_hull_in_is_unresolvable_where_the_plane_is_between_opposed_normals() -> None:
    """The plane's own partiality reaches the patch: no unique chart, so no footprint."""
    cloud = _drifting_cloud(3, rise=0.0)  # a frame at 1/60, between the plane's two samples
    flipping = PlaneSignal.from_samples(
        [0.0, 2 / 60], [PlaneValue(point=[0, 0, 0], normal=[0, 0, 1]), PlaneValue(point=[0, 0, 0], normal=[0, 0, -1])]
    )
    decision = cloud.hull_in(flipping).decide()
    assert isinstance(decision, Unresolvable)
    assert "opposed normals" in decision.reason


def test_hull_in_over_disjoint_supports_is_unresolvable() -> None:
    cloud = _drifting_cloud(3)
    elsewhere = PlaneSignal.from_samples([10.0, 11.0], [_FLAT, _FLAT])
    decision = cloud.hull_in(elsewhere).decide()
    assert isinstance(decision, Unresolvable)
    assert "do not overlap" in decision.reason
