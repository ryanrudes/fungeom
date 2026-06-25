"""Operand-side broadcasts of the ``Plane`` queries over a ``Point3Bundle`` (G7).

These live in the bundle package (which already depends on ``plane``) so the layering DAG stays
acyclic — the ``Plane`` facade dispatches into them lazily when handed a cloud. Each is a
per-key broadcast over the *present* members, so the occlusion mask carries through.
"""

from __future__ import annotations

from dataclasses import dataclass

from fungeom.primitives.bundle.decidability import BundleDecision
from fungeom.primitives.bundle.resolvers.base import decide_mapped
from fungeom.primitives.bundle.resolvers.boolean import BoolBundle
from fungeom.primitives.bundle.resolvers.point3 import Point3Bundle
from fungeom.primitives.bundle.resolvers.scalar import ScalarBundle
from fungeom.primitives.plane.resolvers.base import Plane
from fungeom.primitives.point3.value import Point3Value


@dataclass(frozen=True, eq=False)
class PlaneSignedDistanceBundle(ScalarBundle):
    """Each present point's signed distance to ``plane`` (→ ``ScalarBundle``)."""

    plane: Plane
    cloud: Point3Bundle

    def _decide(self) -> BundleDecision[float]:
        return decide_mapped(self.cloud, lambda key: self.plane.signed_distance(self.cloud.at(key)))


@dataclass(frozen=True, eq=False)
class PlaneProjectBundle(Point3Bundle):
    """Each present point projected orthogonally onto ``plane`` (→ ``Point3Bundle``)."""

    plane: Plane
    cloud: Point3Bundle

    def _decide(self) -> BundleDecision[Point3Value]:
        return decide_mapped(self.cloud, lambda key: self.plane.project(self.cloud.at(key)))


@dataclass(frozen=True, eq=False)
class PlaneContainsBundle(BoolBundle):
    """Whether each present point lies on ``plane`` within ``tolerance`` (→ ``BoolBundle``)."""

    plane: Plane
    cloud: Point3Bundle
    tolerance: float

    def _decide(self) -> BundleDecision[bool]:
        return decide_mapped(self.cloud, lambda key: self.plane.contains(self.cloud.at(key), self.tolerance))
