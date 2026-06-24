"""Frame2 — 2D coordinate frames, grounding, and resolving to world-anchored frames."""

from __future__ import annotations

import numpy as np
import pytest

from fungeom import (
    WORLD_FRAME2,
    CoordinateFrame2,
    Frame2,
    Point2,
    Resolvable,
    RigidTransform2,
    Scalar,
    Transform2,
    Unresolvable,
    Vec2,
)


def _xlate(x: float, y: float) -> RigidTransform2:
    return RigidTransform2.from_translation(np.array([x, y]))


def test_world_known_and_detached() -> None:
    table = WORLD_FRAME2.child("table", _xlate(10, 0))
    decision = Frame2.known(table).decide()
    assert isinstance(decision, Resolvable)
    assert np.allclose(decision.value.to_world().translation, [10, 0])
    assert isinstance(Frame2.detached("loose").decide(), Unresolvable)


def test_world_is_the_root_resolver_and_attach() -> None:
    gripper = Frame2.world.attach("gripper", _xlate(0, 5))  # coerces a bare RigidTransform2
    assert np.allclose(gripper.resolve().to_world().translation, [0, 5])
    tool = Frame2.world.attach("tool", Transform2.translation(Vec2.of(3, 4)))  # a deferred transform
    assert np.allclose(tool.resolve().to_world().translation, [3, 4])


def test_attach_propagates_unresolvability() -> None:
    bad = Transform2.rotation(Scalar.of(1) / Scalar.of(0))
    assert isinstance(Frame2.detached("x").attach("t", _xlate(1, 0)).decide(), Unresolvable)  # bad parent
    assert isinstance(Frame2.world.attach("t", bad).decide(), Unresolvable)  # bad transform


def test_relative_to() -> None:
    a = Frame2.world.attach("a", _xlate(10, 0))
    b = Frame2.world.attach("b", _xlate(0, 5))
    # a's coordinates re-expressed in b: undo b, then apply a
    assert np.allclose(a.relative_to(b).resolve().translation, [10, -5])
    # partial: a frame that isn't grounded has no placement
    assert isinstance(a.relative_to(Frame2.detached("loose")).decide(), Unresolvable)
    assert isinstance(Frame2.detached("loose").relative_to(a).decide(), Unresolvable)


def test_coordinate_frame_value_methods() -> None:
    assert WORLD_FRAME2.is_grounded
    assert WORLD_FRAME2.world() is WORLD_FRAME2  # the root flattens to itself
    table = WORLD_FRAME2.child("table", _xlate(10, 0))
    assert table.is_grounded and table.root is WORLD_FRAME2
    assert np.allclose(table.to_world().translation, [10, 0])
    floating = CoordinateFrame2.detached("floating")
    assert not floating.is_grounded and floating.root is floating
    assert "table" in repr(table) and "parent='world2'" in repr(table)
    with pytest.raises(ValueError, match="not grounded"):
        floating.world()  # cannot world-anchor an ungrounded frame


def test_multi_level_chain_composes_the_whole_parent_chain() -> None:
    # world -> a (rotate 90° CCW) -> b (translate (2,0) in a) -> c (translate (0,1) in b).
    # The to_world() chain must compose all three: a.to_parent @ b.to_parent @ c.to_parent.
    a = Frame2.world.attach("a", Transform2.rotation(np.pi / 2))
    b = a.attach("b", Transform2.translation(Vec2.of(2, 0)))
    c = b.attach("c", Transform2.translation(Vec2.of(0, 1)))
    # a point at the origin of c: T(0,1) -> (0,1), then T(2,0) -> (2,1), then rot90 -> (-1, 2)
    assert np.allclose(Point2.at(0, 0, c).resolve().coord, [-1, 2], atol=1e-9)
    # relative_to between two deep frames also exercises the full chains
    assert np.allclose(c.relative_to(Frame2.world).resolve().translation, [-1, 2], atol=1e-9)


def test_as_frame2_coercion() -> None:
    from fungeom.primitives.frame2.resolvers.known import as_frame2

    assert isinstance(as_frame2(WORLD_FRAME2), Frame2)  # a bare value -> a resolver
    assert as_frame2(Frame2.world) is Frame2.world  # a resolver passes through
