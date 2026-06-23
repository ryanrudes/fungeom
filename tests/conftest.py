"""Shared fixtures for the test suite.

`bad` provides a fresh *Unresolvable* resolver of every primitive type, so any
test can check that a combinator propagates unresolvability without re-deriving
one. `xlate` builds a pure-translation transform value.
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest

from fungeom import (
    CoordinateFrame,
    Direction3,
    Frame,
    Point3,
    RigidTransform,
    Scalar,
    Transform,
    Vec2,
    Vec3,
)


@pytest.fixture
def xlate() -> Callable[[float, float, float], RigidTransform]:
    """Factory for a pure-translation :class:`RigidTransform` value."""

    def make(x: float, y: float, z: float) -> RigidTransform:
        return RigidTransform.from_translation([x, y, z])

    return make


@pytest.fixture
def bad() -> SimpleNamespace:
    """A fresh, *Unresolvable* resolver of each primitive type."""
    return SimpleNamespace(
        scalar=Scalar.of(1) / Scalar.of(0),  # division by zero
        vec3=Vec3.of(0, 0, 0).normalized(),  # zero vector
        vec2=Vec2.of(0, 0).normalized(),
        point3=Point3.at(0, 0, 0, frame=CoordinateFrame.detached("loose")),
        transform=Transform.rotation(Vec3.of(0, 0, 0), Scalar.of(1)),  # zero axis
        direction3=Direction3.of(0, 0, 0),
        frame=Frame.detached("loose"),
    )
