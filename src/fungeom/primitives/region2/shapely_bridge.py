"""The bridge between a :class:`Region2Value` and a shapely (GEOS) geometry.

fungeom *calls* computational geometry, it does not *own* it (the same stance as the SVD fits):
the genuinely hard, degeneracy-laden parts of the 2-D boolean algebra — general polygon
clipping and offsetting over arbitrary simple polygons with holes — are GEOS's job, behind this
thin, total conversion. A region's oriented even-odd rings become a shapely ``Polygon`` /
``MultiPolygon`` and back; lower-dimensional (measure-zero) results are dropped to the empty
region.
"""

from __future__ import annotations

import numpy as np
from shapely import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from fungeom.primitives.region2.value import Region2Value, oriented_ccw, ring_signed_area


def to_shapely(region: Region2Value) -> BaseGeometry:
    """A region's oriented rings as a shapely geometry (each hole assigned to its containing shell)."""
    if region.is_empty:
        return Polygon()
    outers = [ring for ring in region.rings if ring_signed_area(ring) > 0.0]
    holes = [ring for ring in region.rings if ring_signed_area(ring) < 0.0]
    polygons = []
    for outer in outers:
        shell = Polygon(outer)
        contained = [hole for hole in holes if shell.contains(Polygon(hole).representative_point())]
        polygons.append(Polygon(outer, contained))
    return polygons[0] if len(polygons) == 1 else unary_union(polygons)


def _polygons(geom: BaseGeometry) -> list[Polygon]:
    """Every ``Polygon`` in ``geom`` (recursing into multi/collection; dropping lower-dimensional parts)."""
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        return [polygon for part in geom.geoms for polygon in _polygons(part)]
    return []  # a LineString / Point result is measure-zero — it contributes no area


def from_shapely(geom: BaseGeometry) -> Region2Value:
    """A shapely geometry back into oriented even-odd rings (CCW shells, CW holes)."""
    rings = []
    for polygon in _polygons(geom):
        rings.append(oriented_ccw(np.asarray(polygon.exterior.coords[:-1], dtype=float)))
        for interior in polygon.interiors:
            hole = np.asarray(interior.coords[:-1], dtype=float)
            rings.append(hole if ring_signed_area(hole) < 0.0 else hole[::-1].copy())
    return Region2Value(rings=tuple(rings))
