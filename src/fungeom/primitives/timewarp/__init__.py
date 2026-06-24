"""The ``TimeWarp`` primitive — a monotonic, piecewise-linear reparametrization of time."""

from fungeom.primitives.timewarp.resolvers.base import TimeWarp
from fungeom.primitives.timewarp.value import PiecewiseLinearWarp

__all__ = ["TimeWarp", "PiecewiseLinearWarp"]
