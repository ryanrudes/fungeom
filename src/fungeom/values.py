"""The library's resolved *value* types — what ``resolve()`` returns.

Each is also reachable as ``<Primitive>.Value`` (e.g. ``Vec3.Value is Float3``,
``Point3.Value is Point3Value``). That ``.Value`` handle is a PEP 695 ``type``
alias: ideal for **annotations**, but *not* usable at runtime — ``isinstance(x,
Point3.Value)`` raises ``TypeError``. For runtime needs (``isinstance`` checks,
constructing a value directly) import the class from here instead::

    from fungeom.values import Point3Value
    isinstance(p.resolve(), Point3Value)

This module sits at the top level rather than in ``core`` on purpose: it
re-exports *from* primitives, and ``core`` must never depend on primitives. (It is
named ``values`` rather than ``types`` to avoid shadowing the standard library.)
"""

from __future__ import annotations

from fungeom.core.arrays import ArrayLike, freeze
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.coverage.value import CoverageValue
from fungeom.primitives.direction3.value import Direction3Value
from fungeom.primitives.frame.value import CoordinateFrame
from fungeom.primitives.interval.value import IntervalValue
from fungeom.primitives.point3.value import Point3Value
from fungeom.primitives.sampling.value import SamplingValue
from fungeom.primitives.signals.series import SampledSeries
from fungeom.primitives.timeline.value import Clock
from fungeom.primitives.timemap.value import AffineTimeMap
from fungeom.primitives.timewarp.value import PiecewiseLinearWarp
from fungeom.primitives.transform.value import Mat3, Mat4, RigidTransform
from fungeom.primitives.vec2.value import Float2
from fungeom.primitives.vec3.value import Float3

__all__ = [
    "Float2",
    "Float3",
    "Mat3",
    "Mat4",
    "RigidTransform",
    "CoordinateFrame",
    "Point3Value",
    "Direction3Value",
    "IntervalValue",
    "CoverageValue",
    "AffineTimeMap",
    "PiecewiseLinearWarp",
    "BundleValue",
    "Clock",
    "SamplingValue",
    "SampledSeries",
    "ArrayLike",
    "freeze",
]
