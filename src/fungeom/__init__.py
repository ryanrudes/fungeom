"""fungeom — a functional geometry API.

Geometry is described as an immutable, lazily-evaluated graph of resolvers. Each
primitive is one class — ``Scalar``, ``Vec2``, ``Vec3``, ``Direction3``,
``Transform``, ``Frame``, ``Point3`` — that you both construct from (classmethods
like ``Vec3.of`` / ``Point3.at``) and compose with (fluent methods like
``a.midpoint(b)``). Build a graph, ``decide()`` whether it can be resolved, then
``resolve()`` to get a concrete value (reachable as ``<Primitive>.Value``).

The decidability core (``Resolver``, ``Resolvable``, ``Unresolvable``,
``gather``) is public; the concrete resolvers behind each facade are not.
"""

from fungeom.core import (
    Resolvability,
    Resolvable,
    Resolver,
    Unresolvable,
    UnresolvableError,
    gather,
)
from fungeom.primitives import (
    WORLD_FRAME,
    CoordinateFrame,
    Direction3,
    Frame,
    Mat3,
    Mat4,
    Point3,
    RigidTransform,
    Scalar,
    Transform,
    Vec2,
    Vec3,
)
from fungeom.viz import render_tree, resolver_tree

__all__ = [
    # primitives (facades)
    "Scalar",
    "Vec2",
    "Vec3",
    "Direction3",
    "Transform",
    "Frame",
    "Point3",
    # commonly-used value types
    "RigidTransform",
    "CoordinateFrame",
    "WORLD_FRAME",
    "Mat3",
    "Mat4",
    # decidability core
    "Resolver",
    "Resolvability",
    "Resolvable",
    "Unresolvable",
    "UnresolvableError",
    "gather",
    # visualization
    "resolver_tree",
    "render_tree",
]
