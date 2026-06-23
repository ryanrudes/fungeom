"""Point3 — framed positions, world-anchoring, and the point combinators."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import numpy as np
import pytest

from fungeom import (
    WORLD_FRAME,
    CoordinateFrame,
    Frame,
    Point3,
    RigidTransform,
    Scalar,
    Transform,
    Unresolvable,
    Vec3,
)


# --- construction ----------------------------------------------------------


def test_at_dispatches_literal_vs_graph() -> None:
    assert type(Point3.at(1, 2, 3)).__name__ == "LocatedPoint3"  # all numbers, value frame
    assert type(Point3.at(Scalar.of(1), 2, 3)).__name__ == "FramedPoint3"  # deferred coord
    assert type(Point3.at(1, 2, 3, frame=Frame.world)).__name__ == "FramedPoint3"  # resolver frame


def test_at_with_deferred_coordinates() -> None:
    r = Vec3.of(0, 3, 4).norm()  # a Scalar -> 5
    assert np.allclose(Point3.at(r, 0.0, r / Scalar.of(2)).resolve().coord, [5, 0, 2.5])


def test_at_with_a_frame_resolver() -> None:
    placed = Frame.world.attach("table", Transform.translation([10, 0, 0]))
    assert np.allclose(Point3.at(0, 1, 0, frame=placed).resolve().coord, [10, 1, 0])


def test_in_frame_with_a_deferred_frame() -> None:
    frame = Frame.world.attach("tool", Transform.translation(Vec3.of(10, 0, 0)))
    assert np.allclose(Point3.in_frame(Vec3.of(0, 1, 0), frame).resolve().coord, [10, 1, 0])


def test_world_anchoring(xlate: Callable[..., RigidTransform]) -> None:
    table = WORLD_FRAME.child("table", xlate(10, 0, 0))
    resolved = Point3.at(0, 0, 0, frame=table).resolve()
    assert np.allclose(resolved.coord, [10, 0, 0])
    assert resolved.frame is WORLD_FRAME


# --- combinators -----------------------------------------------------------


def test_midpoint_lerp_translate() -> None:
    a, b = Point3.at(0, 0, 0), Point3.at(10, 0, 0)
    assert np.allclose(a.midpoint(b).resolve().coord, [5, 0, 0])
    assert np.allclose(a.lerp(b, 0.25).resolve().coord, [2.5, 0, 0])
    assert np.allclose(a.translate(Vec3.of(1, 2, 3)).resolve().coord, [1, 2, 3])


def test_displacement_distance_direction() -> None:
    a, b = Point3.at(0, 0, 0), Point3.at(0, 3, 4)
    assert np.allclose(a.displacement_to(b).resolve(), [0, 3, 4])
    assert a.distance_to(b).resolve() == 5.0
    assert np.allclose(a.direction_to(b).resolve().vector, [0, 0.6, 0.8])


def test_centroid_list_generator_and_empty() -> None:
    pts = [Point3.at(0, 0, 0), Point3.at(3, 0, 0), Point3.at(0, 3, 0)]
    assert np.allclose(Point3.centroid(pts).resolve().coord, [1, 1, 0])
    assert np.allclose(Point3.centroid(Point3.at(i, 0, 0) for i in range(5)).resolve().coord, [2, 0, 0])
    assert isinstance(Point3.centroid([]).decide(), Unresolvable)


def test_affine_combination() -> None:
    pts = [Point3.at(0, 0, 0), Point3.at(4, 0, 0)]
    assert np.allclose(Point3.affine(pts, [1, 3]).resolve().coord, [3, 0, 0])
    assert np.allclose(Point3.affine(pts, [1, 1]).resolve().coord, [2, 0, 0])  # == centroid
    assert isinstance(Point3.affine(pts, [1, -1]).decide(), Unresolvable)  # zero total weight
    assert isinstance(Point3.affine([], []).decide(), Unresolvable)  # no points
    with pytest.raises(ValueError):
        Point3.affine(pts, [1])  # mismatched lengths


# --- resolvability propagation --------------------------------------------


def test_propagation(bad: object) -> None:
    a = Point3.at(0, 0, 0)
    assert isinstance(a.midpoint(bad.point3).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(bad.point3.midpoint(a).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(a.lerp(a, bad.scalar).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(a.displacement_to(bad.point3).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(a.direction_to(a).decide(), Unresolvable)  # coincident points
    assert isinstance(Point3.at(bad.scalar, 0, 0).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(Point3.centroid([a, bad.point3]).decide(), Unresolvable)  # type: ignore[attr-defined]
    assert isinstance(Point3.affine([a, bad.point3], [1, 1]).decide(), Unresolvable)  # type: ignore[attr-defined]


# --- value type behavior ---------------------------------------------------


def test_point_value_is_immutable() -> None:
    p = Point3.at(1.0, 2.0, 3.0).resolve()
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.frame = WORLD_FRAME  # type: ignore[misc]
    with pytest.raises(ValueError):
        p.coord[0] = 99.0


def test_point_value_to_frame_and_repr(xlate: Callable[..., RigidTransform]) -> None:
    table = WORLD_FRAME.child("table", xlate(5, 0, 0))
    p = Point3.at(1, 2, 3).resolve()
    q = p.to_frame(table)
    assert np.allclose(q.coord, [-4, 2, 3])
    assert p.approx_equal(q)
    assert "Point3Value" in repr(p)
    with pytest.raises(ValueError):
        p.to_frame(CoordinateFrame.detached("other_tree"))  # different frame trees


def test_point_value_world_requires_grounded_frame() -> None:
    from fungeom.values import Point3Value

    ungrounded = Point3Value.of(0, 0, 0, frame=CoordinateFrame.detached("loose"))
    with pytest.raises(ValueError):
        ungrounded.world()
