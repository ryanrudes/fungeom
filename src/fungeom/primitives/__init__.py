"""Geometric primitives, each a submodule with the same shape.

Every primitive is one **facade class** (the resolver) with classmethod
constructors and fluent combinators; its resolved value is reachable as
``<Primitive>.Value``. Concrete resolvers live behind the facade (one file each
under ``<primitive>/resolvers/``) and are not part of the public surface.

Submodules: ``boolean``, ``scalar``, ``vec2``, ``vec3``, ``direction3``, ``transform``,
``frame``, ``point3``, plus the temporal ``duration`` / ``instant`` / ``interval``
/ ``coverage`` / ``timemap`` / ``timeline`` / ``sampling`` and the ``signals``
package (scalar / vec3 / direction3 / transform / point3, over one generic core).
"""

from fungeom.primitives.boolean import Bool
from fungeom.primitives.coverage import Coverage, CoverageValue
from fungeom.primitives.direction2 import Direction2, Direction2Value
from fungeom.primitives.direction3 import Direction3, Direction3Value
from fungeom.primitives.duration import Duration
from fungeom.primitives.frame import WORLD_FRAME, CoordinateFrame, Frame
from fungeom.primitives.frame2 import WORLD_FRAME2, CoordinateFrame2, Frame2
from fungeom.primitives.instant import Instant
from fungeom.primitives.interval import Interval, IntervalValue
from fungeom.primitives.line import Line, LineValue
from fungeom.primitives.plane import Plane, PlaneValue
from fungeom.primitives.point2 import Point2, Point2Value
from fungeom.primitives.point3 import Point3, Point3Value
from fungeom.primitives.ray import Ray, RayValue
from fungeom.primitives.sampling import Sampling, SamplingValue
from fungeom.primitives.segment import Segment, SegmentValue
from fungeom.primitives.scalar import Scalar
from fungeom.primitives.signals import (
    Boundary,
    Direction3Signal,
    Interpolation,
    Point3BundleSignal,
    Point3Signal,
    SampledSeries,
    ScalarSignal,
    TransformSignal,
    Vec3Signal,
)
from fungeom.primitives.timeline import MASTER_CLOCK, Clock, Timeline
from fungeom.primitives.bundle import (
    Bundle,
    BundleValue,
    Direction3Bundle,
    Point3Bundle,
    ScalarBundle,
    TransformBundle,
    Vec3Bundle,
)
from fungeom.primitives.timemap import AffineTimeMap, TimeMap
from fungeom.primitives.timewarp import PiecewiseLinearWarp, TimeWarp
from fungeom.primitives.transform import Mat3, Mat4, RigidTransform, Transform
from fungeom.primitives.transform2 import Mat2, RigidTransform2, Transform2
from fungeom.primitives.vec2 import Float2, Vec2
from fungeom.primitives.vec3 import Float3, Vec3

__all__ = [
    # facades
    "Bool",
    "Scalar",
    "Vec2",
    "Vec3",
    "Direction2",
    "Direction3",
    "Transform",
    "Transform2",
    "Frame",
    "Frame2",
    "Point2",
    "Point3",
    "Plane",
    "Line",
    "Ray",
    "Segment",
    # temporal
    "Duration",
    "Instant",
    "Interval",
    "Coverage",
    "TimeMap",
    "TimeWarp",
    "Timeline",
    "Sampling",
    "Bundle",
    "ScalarBundle",
    "Vec3Bundle",
    "Direction3Bundle",
    "TransformBundle",
    "Point3Bundle",
    "Point3BundleSignal",
    "Interpolation",
    "Boundary",
    "ScalarSignal",
    "Vec3Signal",
    "Direction3Signal",
    "TransformSignal",
    "Point3Signal",
    # value types
    "IntervalValue",
    "CoverageValue",
    "AffineTimeMap",
    "PiecewiseLinearWarp",
    "Clock",
    "MASTER_CLOCK",
    "SamplingValue",
    "SampledSeries",
    "BundleValue",
    "Float2",
    "Float3",
    "Mat2",
    "Mat3",
    "Mat4",
    "RigidTransform",
    "RigidTransform2",
    "CoordinateFrame",
    "WORLD_FRAME",
    "CoordinateFrame2",
    "WORLD_FRAME2",
    "Point2Value",
    "Point3Value",
    "PlaneValue",
    "LineValue",
    "RayValue",
    "SegmentValue",
    "Direction2Value",
    "Direction3Value",
]
