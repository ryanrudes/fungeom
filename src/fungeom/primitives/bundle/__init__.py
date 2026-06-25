"""The ``Bundle`` primitive — a finite, keyed collection (a field over a nominal axis)."""

from fungeom.primitives.bundle.resolvers.base import Bundle
from fungeom.primitives.bundle.resolvers.boolean import BoolBundle
from fungeom.primitives.bundle.resolvers.direction3 import Direction3Bundle
from fungeom.primitives.bundle.resolvers.point2 import Point2Bundle
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle
from fungeom.primitives.bundle.resolvers.transform import TransformBundle
from fungeom.primitives.bundle.resolvers.vec3 import Vec3Bundle
from fungeom.primitives.bundle.value import BundleValue

__all__ = [
    "Bundle",
    "BundleValue",
    "ScalarBundle",
    "BoolBundle",
    "Vec3Bundle",
    "Direction3Bundle",
    "TransformBundle",
    "Point2Bundle",
    "Point3Bundle",
]
