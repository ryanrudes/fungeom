"""The ``Bundle`` primitive — a finite, keyed collection (a field over a nominal axis)."""

from fungeom.primitives.bundle.resolvers.base import Bundle
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.bundle.value import BundleValue

__all__ = ["Bundle", "Point3Bundle", "BundleValue"]
