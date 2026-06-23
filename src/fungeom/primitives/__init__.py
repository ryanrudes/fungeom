"""Geometric primitives, each a submodule with the same shape.

Every primitive is one **facade class** (the resolver) with classmethod
constructors and fluent combinators; its resolved value is reachable as
``<Primitive>.Value``. Concrete resolvers live behind the facade (one file each
under ``<primitive>/resolvers/``) and are not part of the public surface.

Submodules: ``scalar``, ``vec2``, ``vec3``, ``direction3``, ``transform``,
``frame``, ``point3``.
"""

from fungeom.primitives.direction3 import Direction3, Direction3Value
from fungeom.primitives.frame import WORLD_FRAME, CoordinateFrame, Frame
from fungeom.primitives.point3 import Point3, Point3Value
from fungeom.primitives.scalar import Scalar
from fungeom.primitives.transform import Mat3, Mat4, RigidTransform, Transform
from fungeom.primitives.vec2 import Float2, Vec2
from fungeom.primitives.vec3 import Float3, Vec3

__all__ = [
    # facades
    "Scalar",
    "Vec2",
    "Vec3",
    "Direction3",
    "Transform",
    "Frame",
    "Point3",
    # value types
    "Float2",
    "Float3",
    "Mat3",
    "Mat4",
    "RigidTransform",
    "CoordinateFrame",
    "WORLD_FRAME",
    "Point3Value",
    "Direction3Value",
]
