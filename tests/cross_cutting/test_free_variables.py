"""Free-variable leaves compose through the whole algebra and bind to a concrete result.

The keystone acceptance, lifted straight from the retarget spike that motivated the feature
(``docs/fungeom-free-variables-spec.md`` over in that repo): author a geometric construction
as pure data over *free* point leaves, then ``resolve_in`` an environment of their positions
and get exactly the value you'd get had you built it from concrete points. The op chain here
— ``Point3Bundle.of(frees) -> fit_plane -> in_frame -> Region2.hull -> Face.on`` — is the real
one a motion-capture *contact patch* is built from, so this proves the entire downstream
algebra accepts free leaves with no per-op support.
"""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    Face,
    Point3,
    Point3Bundle,
    Region2,
    Resolvable,
    Unresolvable,
    UnresolvableError,
)

# Three markers, referenced by their own object identity (no strings, no wrapper).
HEEL, TOE, MID = object(), object(), object()
POSITIONS = {HEEL: (0.0, 0.0, 0.0), TOE: (1.0, 0.0, 0.0), MID: (0.0, 1.0, 0.0)}


def _sole(points: dict[object, Point3]) -> Face:
    """The real patch construction, over whatever ``Point3``s are supplied (free or concrete)."""
    cloud = Point3Bundle.of([points[HEEL], points[TOE], points[MID]])
    plane = cloud.fit_plane()
    return Face.on(plane, Region2.hull(cloud.in_frame(plane)))


def _env() -> dict[object, Point3]:
    return {marker: Point3.at(*coord) for marker, coord in POSITIONS.items()}


def test_face_over_free_leaves_is_identical_to_face_over_concrete_points() -> None:
    # (1) the canonical criterion: data-over-frees, resolved, == built-from-concretes.
    free_face = _sole({marker: Point3.free(marker) for marker in POSITIONS})
    concrete_face = _sole({marker: Point3.at(*coord) for marker, coord in POSITIONS.items()})

    resolved = free_face.resolve_in(_env())
    expected = concrete_face.resolve()

    assert np.allclose(resolved.plane.point, expected.plane.point)
    assert np.allclose(resolved.plane.normal, expected.plane.normal)
    assert np.allclose(resolved.region.rings[0], expected.region.rings[0])

    # And through the read-back surface retarget actually uses (plane / region / boundary).
    bound = free_face.bind(_env())
    assert isinstance(bound, Face)  # bind preserves the primitive type — a Face flows on unchanged
    assert np.allclose(bound.plane().resolve().normal, concrete_face.plane().resolve().normal)
    free_boundary = bound.boundary().resolve()
    conc_boundary = concrete_face.boundary().resolve()
    assert free_boundary.support() == conc_boundary.support()
    for key in conc_boundary.support():
        assert np.allclose(free_boundary.members[key].coord, conc_boundary.members[key].coord)


def test_missing_free_is_unresolvable_naming_the_variable() -> None:
    # (2) partiality stays honest: an unbound marker names itself, not a stray KeyError.
    free_face = _sole({marker: Point3.free(marker) for marker in POSITIONS})
    partial = {HEEL: Point3.at(0, 0, 0), TOE: Point3.at(1, 0, 0)}  # MID missing

    decision = free_face.decide_in(partial)
    assert isinstance(decision, Unresolvable)
    assert repr(MID) in decision.reason
    assert free_face.free_variables() == frozenset((HEEL, TOE, MID))  # introspectable before binding
    with pytest.raises(UnresolvableError):
        free_face.resolve_in(partial)


def test_plane_and_region_ops_accept_free_leaves() -> None:
    # The rest of the op table the motivating patch composes — Plane.facing / .flipped /
    # .offset and Region2.hull(...).offset — must also bind structurally over free leaves.
    apex = object()  # an off-plane reference for .facing, itself a free leaf
    apex_pos = (0.0, 0.0, 1.0)

    def patch(points: dict[object, Point3], toward: Point3) -> Face:
        cloud = Point3Bundle.of([points[HEEL], points[TOE], points[MID]])
        plane = cloud.fit_plane().facing(toward).flipped().offset(0.01)
        region = Region2.hull(cloud.in_frame(plane)).offset(0.005)
        return Face.on(plane, region)

    free = patch({marker: Point3.free(marker) for marker in POSITIONS}, Point3.free(apex))
    concrete = patch({m: Point3.at(*c) for m, c in POSITIONS.items()}, Point3.at(*apex_pos))
    assert isinstance(free.decide(), Unresolvable)  # unbound until the markers arrive
    assert free.free_variables() == frozenset((HEEL, TOE, MID, apex))

    env = {**_env(), apex: Point3.at(*apex_pos)}
    resolved, expected = free.resolve_in(env), concrete.resolve()
    assert np.allclose(resolved.plane.point, expected.plane.point)
    assert np.allclose(resolved.plane.normal, expected.plane.normal)
    assert np.allclose(resolved.region.rings[0], expected.region.rings[0])


def test_fit_plane_over_three_free_points() -> None:
    # (3) the canonical sub-case: a plane fit over three free points resolves to the plane
    # through their bound positions (here the z = 0 plane).
    a, b, c = object(), object(), object()
    plane = Point3Bundle.of([Point3.free(a), Point3.free(b), Point3.free(c)]).fit_plane()
    assert isinstance(plane.decide(), Unresolvable)  # nothing to fit yet
    env = {a: Point3.at(0, 0, 0), b: Point3.at(1, 0, 0), c: Point3.at(0, 1, 0)}
    assert isinstance(plane.decide_in(env), Resolvable)
    value = plane.resolve_in(env)
    assert np.isclose(abs(np.dot(value.normal, [0, 0, 1])), 1.0)  # normal is ±z
    assert np.isclose(value.point[2], 0.0)  # the fitted plane passes through z = 0
