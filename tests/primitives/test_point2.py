"""Point2 — a framed 2D position and its combinators."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    WORLD_FRAME2,
    CoordinateFrame2,
    Frame2,
    Point2,
    RigidTransform2,
    Scalar,
    Transform2,
    Unresolvable,
    Vec2,
)
from fungeom.values import Point2Value


def test_constructors() -> None:
    assert np.allclose(Point2.at(3, 4).resolve().coord, [3, 4])
    # deferred coordinate -> a graph
    assert np.allclose(Point2.at(Scalar.of(3), 4).resolve().coord, [3, 4])
    assert np.allclose(Point2.in_frame(Vec2.of(1, 2)).resolve().coord, [1, 2])
    assert np.allclose(Point2.centroid([Point2.at(0, 0), Point2.at(3, 0), Point2.at(0, 3)]).resolve().coord, [1, 1])
    assert np.allclose(Point2.affine([Point2.at(0, 0), Point2.at(4, 0)], [1, 1]).resolve().coord, [2, 0])


def test_constructor_partiality() -> None:
    assert "no points" in Point2.centroid([]).decide().reason
    assert "no points" in Point2.affine([], []).decide().reason
    assert "zero total weight" in Point2.affine([Point2.at(0, 0), Point2.at(4, 0)], [1, -1]).decide().reason
    with pytest.raises(ValueError, match="same length"):
        Point2.affine([Point2.at(0, 0)], [1, 1])
    # a literal point in a detached *value* frame is the LocatedPoint2 ungrounded branch
    detached_value = Point2.at(0, 0, CoordinateFrame2.detached("vframe"))
    assert "not grounded" in detached_value.decide().reason


def test_combinators() -> None:
    origin = Point2.at(0, 0)
    far = Point2.at(3, 4)
    assert origin.distance_to(far).resolve() == 5.0
    assert np.allclose(origin.displacement_to(far).resolve(), [3, 4])
    assert np.allclose(origin.direction_to(far).resolve().vector, [0.6, 0.8])
    assert np.allclose(origin.midpoint(far).resolve().coord, [1.5, 2.0])
    assert np.allclose(origin.lerp(far, 0.25).resolve().coord, [0.75, 1.0])
    assert np.allclose(Point2.at(1, 1).translate(Vec2.of(2, 3)).resolve().coord, [3, 4])
    assert np.allclose(Point2.at(1, 1).translate(np.array([2.0, 3.0])).resolve().coord, [3, 4])  # raw array
    assert np.allclose(Point2.at(1, 0).reflect_across(Point2.at(0, 0)).resolve().coord, [-1, 0])
    # transformed_by a 2D motion
    rotated = Point2.at(1, 0).transformed_by(Transform2.rotation(np.pi / 2)).resolve()
    assert np.allclose(rotated.coord, [0, 1], atol=1e-9)


def test_direction_to_coincident_is_unresolvable() -> None:
    decision = Point2.at(1, 1).direction_to(Point2.at(1, 1)).decide()
    assert isinstance(decision, Unresolvable)
    assert "zero vector" in decision.reason


def test_frames_and_grounding() -> None:
    cam = Frame2.world.attach("cam", Transform2.translation(Vec2.of(10, 0)))
    assert np.allclose(Point2.at(1, 1, cam).resolve().coord, [11, 1])  # world-anchored
    loose = Frame2.detached("loose")
    decision = Point2.at(0, 0, loose).decide()
    assert isinstance(decision, Unresolvable)
    assert "not grounded" in decision.reason


def test_value_methods() -> None:
    cam = WORLD_FRAME2.child("cam", RigidTransform2.from_translation(np.array([10.0, 0.0])))
    local = Point2Value.of(1, 1, frame=cam)
    assert np.allclose(local.world().coord, [11, 1])
    assert local.is_grounded
    # re-express in another frame in the same tree (round trip)
    back = local.world().to_frame(cam)
    assert np.allclose(back.coord, [1, 1])
    assert local.approx_equal(Point2.at(11, 1).resolve())
    assert repr(Point2.at(2, 3).resolve()) == "Point2Value([2, 3], frame='world2')"
    floating = CoordinateFrame2.detached("floating")
    with pytest.raises(ValueError, match="not grounded"):
        Point2Value.of(0, 0, frame=floating).world()


def test_to_frame_across_trees_raises() -> None:
    other_tree = CoordinateFrame2.detached("other")
    with pytest.raises(ValueError, match="different trees"):
        Point2.at(1, 1).resolve().to_frame(other_tree)
