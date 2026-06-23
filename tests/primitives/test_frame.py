"""Frame — coordinate frames, grounding, and resolving to world-anchored frames."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from fungeom import (
    WORLD_FRAME,
    CoordinateFrame,
    Frame,
    Resolvable,
    RigidTransform,
    Transform,
    Unresolvable,
    Vec3,
)


def test_world_known_and_detached(xlate: Callable[..., RigidTransform]) -> None:
    table = WORLD_FRAME.child("table", xlate(10, 0, 0))
    decision = Frame.known(table).decide()
    assert isinstance(decision, Resolvable)
    assert np.allclose(decision.value.to_world().translation, [10, 0, 0])
    assert isinstance(Frame.detached("loose").decide(), Unresolvable)


def test_world_is_the_root_resolver_and_attach(xlate: Callable[..., RigidTransform]) -> None:
    gripper = Frame.world.attach("gripper", xlate(0, 5, 0))  # coerces a bare RigidTransform
    assert np.allclose(gripper.resolve().to_world().translation, [0, 5, 0])
    tool = Frame.world.attach("tool", Transform.translation(Vec3.of(0, 3, 4)))  # a deferred transform
    assert np.allclose(tool.resolve().to_world().translation, [0, 3, 4])


def test_attach_propagates_unresolvability(bad: object, xlate: Callable[..., RigidTransform]) -> None:
    assert isinstance(Frame.detached("x").attach("t", xlate(1, 0, 0)).decide(), Unresolvable)  # bad parent
    assert isinstance(Frame.world.attach("t", bad.transform).decide(), Unresolvable)  # type: ignore[attr-defined]


def test_coordinate_frame_value_methods(xlate: Callable[..., RigidTransform]) -> None:
    assert WORLD_FRAME.is_grounded
    assert WORLD_FRAME.world() is WORLD_FRAME  # the root flattens to itself
    table = WORLD_FRAME.child("table", xlate(10, 0, 0))
    assert table.is_grounded and table.root is WORLD_FRAME
    assert np.allclose(table.to_world().translation, [10, 0, 0])
    floating = CoordinateFrame.detached("floating")
    assert not floating.is_grounded and floating.root is floating
    assert "table" in repr(table) and "parent='world'" in repr(table)
    import pytest

    with pytest.raises(ValueError):
        floating.world()  # cannot world-anchor an ungrounded frame
