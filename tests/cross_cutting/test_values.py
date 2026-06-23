"""The `fungeom.values` module — runtime-usable resolved value types.

Unlike ``<Primitive>.Value`` (a PEP 695 alias, annotation-only), these are real
classes/aliases you can ``isinstance``-check against.
"""

from __future__ import annotations

import numpy as np

import fungeom.values as values
from fungeom import Direction3, Point3, Transform, Vec3
from fungeom.values import CoordinateFrame, Direction3Value, Point3Value, RigidTransform


def test_values_reexports_the_resolved_types() -> None:
    assert isinstance(Point3.at(1, 2, 3).resolve(), Point3Value)
    assert isinstance(Direction3.of(0, 0, 1).resolve(), Direction3Value)
    assert isinstance(Transform.identity().resolve(), RigidTransform)
    assert isinstance(Vec3.of(1, 2, 3).resolve(), np.ndarray)  # Vec3.Value is the array type
    # the module re-exports everything it advertises
    assert set(values.__all__) <= set(dir(values))


def test_value_is_annotation_only_at_runtime() -> None:
    # The point of the `values` module: Point3.Value can't be used at runtime.
    import pytest

    with pytest.raises(TypeError):
        isinstance(Point3.at(0, 0, 0).resolve(), Point3.Value)  # type: ignore[arg-type]
    # ...but the real class works:
    assert isinstance(Point3.at(0, 0, 0).resolve(), Point3Value)
    assert CoordinateFrame is not None
