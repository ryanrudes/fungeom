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
    Coverage,
    Direction3,
    Direction3Signal,
    Duration,
    Frame,
    Instant,
    Interval,
    Point3,
    Point3Signal,
    RigidTransform,
    Sampling,
    Scalar,
    ScalarSignal,
    TimeMap,
    TimeWarp,
    Timeline,
    Transform,
    TransformSignal,
    Vec2,
    Vec3,
    Vec3Signal,
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
        boolean=Scalar.of(1).lt(Scalar.of(1) / Scalar.of(0)),  # comparison of an unresolvable scalar
        vec3=Vec3.of(0, 0, 0).normalized(),  # zero vector
        vec2=Vec2.of(0, 0).normalized(),
        point3=Point3.at(0, 0, 0, frame=CoordinateFrame.detached("loose")),
        transform=Transform.rotation(Vec3.of(0, 0, 0), Scalar.of(1)),  # zero axis
        direction3=Direction3.of(0, 0, 0),
        frame=Frame.detached("loose"),
        duration=Duration.of(1).scale(Scalar.of(1) / Scalar.of(0)),  # scaled by an unresolvable scalar
        instant=Instant.epoch.shifted_by(Duration.of(1).scale(Scalar.of(1) / Scalar.of(0))),
        interval=Interval.between(Instant.at(5), Instant.at(0)),  # end before start
        coverage=Coverage.of([Interval.between(Instant.at(5), Instant.at(0))]),  # bad member
        timemap=TimeMap.rate(0).inverse(),  # zero-rate map has no inverse
        timewarp=TimeWarp.through([(1.0, 0.0), (0.0, 1.0)]),  # non-monotonic source knots
        timeline=Timeline.detached("loose"),  # not synced to the master clock
        sampling=Sampling.at_times([1.0, 0.0]),  # out-of-order timestamps
        scalar_signal=ScalarSignal.from_samples([1.0, 0.0], [1.0, 2.0]),  # bad sampling
        vec3_signal=Vec3Signal.from_samples([1.0, 0.0], [[1.0, 0, 0], [2.0, 0, 0]]),  # bad sampling
        direction3_signal=Direction3Signal.from_samples([1.0, 0.0], [[1, 0, 0], [0, 1, 0]]),  # bad sampling
        transform_signal=TransformSignal.from_samples(
            [1.0, 0.0], [RigidTransform.identity(), RigidTransform.identity()]
        ),  # bad sampling
        point3_signal=Point3Signal.from_samples([1.0, 0.0], [[0, 0, 0], [1, 1, 1]]),  # bad sampling
    )
