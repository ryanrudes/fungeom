"""The signal layer — values that vary over time.

Every signal is a thin facade over one generic, value-type-agnostic core
(:mod:`~fungeom.primitives.signals.series`): a ``Signal[V]`` resolves to a
``SampledSeries[V]`` and is read between samples by an :class:`Interpolation`
kernel that defers the actual combination to the value type's
:class:`Blend` (and beyond its ends by a :class:`Boundary`). Adding a value type
is a small facade plus a blend; flat (scalar/vector), spherical (direction),
SE(3) (transform), and framed (point) value types all share the same machinery,
with their idiosyncratic partialities surfacing as ordinary ``Unresolvable``.
"""

from fungeom.primitives.signals.blend import Blend
from fungeom.primitives.signals.boundary import Boundary
from fungeom.primitives.signals.direction3 import Direction3Signal
from fungeom.primitives.signals.interpolation import Interpolation
from fungeom.primitives.signals.point3 import Point3Signal
from fungeom.primitives.signals.scalar import ScalarSignal
from fungeom.primitives.signals.series import SampledSeries, Signal
from fungeom.primitives.signals.boolean import BoolSeries, BoolSignal
from fungeom.primitives.signals.plane import PlaneSignal
from fungeom.primitives.signals.bundle import Point3BundleSignal, ScalarBundleSignal, TransformBundleSignal
from fungeom.primitives.signals.face import FaceSignal
from fungeom.primitives.signals.transform import TransformSignal
from fungeom.primitives.signals.vec3 import Vec3Signal

__all__ = [
    "Signal",
    "SampledSeries",
    "Blend",
    "Interpolation",
    "Boundary",
    "ScalarSignal",
    "BoolSignal",
    "BoolSeries",
    "Vec3Signal",
    "Direction3Signal",
    "TransformSignal",
    "Point3Signal",
    "PlaneSignal",
    "FaceSignal",
    "Point3BundleSignal",
    "ScalarBundleSignal",
    "TransformBundleSignal",
]
