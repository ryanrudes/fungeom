"""The region2 *value*: a bounded planar area, the 2D spatial sibling of ``CoverageValue``.

A :class:`Region2Value` is a bounded region of the plane represented as a set of oriented
simple-polygon **rings** — counter-clockwise *outer* boundaries and clockwise *holes* — with
the area filled by the even-odd rule (a point inside an outer ring but inside a hole is
*out*). This is to ``point2``/``segment2`` what :class:`~fungeom.values.CoverageValue` (a union
of disjoint intervals) is to ``Instant``/``Duration``: the bounded-area member of the 2D family.

Coordinates are bare 2D numbers in a region-local chart (frame-agnostic — a ``Plane`` /
``Face`` supplies the embedding). The deferred counterpart, a ``Region2`` that resolves to a
``Region2Value``, lives in :mod:`fungeom.primitives.region2.resolvers`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from fungeom.core.arrays import freeze
from fungeom.primitives.vec2.value import Float2, as_vec2

type Ring = np.ndarray
"""A closed simple polygon as a ``(k, 2)`` float array of vertices (no repeated closing point)."""


def ring_signed_area(ring: Ring) -> float:
    """The signed area of ``ring`` by the shoelace formula (positive = counter-clockwise)."""
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def oriented_ccw(ring: Ring) -> Ring:
    """``ring`` reversed if needed so its vertices wind counter-clockwise (positive area)."""
    return ring if ring_signed_area(ring) > 0.0 else ring[::-1].copy()


def ring_centroid_and_area(ring: Ring) -> tuple[Float2, float]:
    """The area-weighted centroid and signed area of ``ring`` (the polygon centroid formula)."""
    x, y = ring[:, 0], ring[:, 1]
    nx, ny = np.roll(x, -1), np.roll(y, -1)
    cross = x * ny - nx * y
    area = 0.5 * float(np.sum(cross))
    centroid = np.array([float(np.sum((x + nx) * cross)), float(np.sum((y + ny) * cross))]) / (6.0 * area)
    return as_vec2(centroid), area


def _on_segment(a: Float2, b: Float2, p: Float2, tol: float) -> bool:
    """Whether ``p`` lies on the closed segment ``a``–``b`` within ``tol``."""
    ab = b - a
    ap = p - a
    cross = float(ab[0] * ap[1] - ab[1] * ap[0])
    length = float(np.hypot(*ab))  # rings never have zero-length edges (distinct vertices enforced)
    if abs(cross) / length > tol:
        return False
    t = float(np.dot(ap, ab)) / (length * length)
    return -tol <= t <= 1.0 + tol


def _closest_on_segment(a: Float2, b: Float2, p: Float2) -> Float2:
    """The point on the closed segment ``a``–``b`` nearest to ``p`` (parameter clamped to [0, 1])."""
    ab = b - a
    denom = float(np.dot(ab, ab))  # rings never have zero-length edges (distinct vertices enforced)
    t = float(np.clip(np.dot(p - a, ab) / denom, 0.0, 1.0))
    return a + t * ab


def point_in_rings(rings: Sequence[Ring], p: Float2, tol: float = 1e-9) -> bool:
    """Whether ``p`` is inside the area (even-odd rule); a boundary point counts as inside."""
    inside = False
    for ring in rings:
        n = len(ring)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            if _on_segment(a, b, p, tol):
                return True  # on the boundary → closed region contains it
            if (a[1] > p[1]) != (b[1] > p[1]):
                x_cross = a[0] + (p[1] - a[1]) / (b[1] - a[1]) * (b[0] - a[0])
                if p[0] < x_cross:
                    inside = not inside
    return inside


def _segments_properly_intersect(a: Float2, b: Float2, c: Float2, d: Float2) -> bool:
    """Whether open segments ``a``–``b`` and ``c``–``d`` cross at an interior point."""

    def orient(p: Float2, q: Float2, r: Float2) -> float:
        return float((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))

    d1, d2, d3, d4 = orient(c, d, a), orient(c, d, b), orient(a, b, c), orient(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def boundary_samples(rings: Sequence[Ring], count: int) -> list[Float2]:
    """``count`` points spaced evenly by arc length around the rings' combined boundary."""
    segments = [(ring[i], ring[(i + 1) % len(ring)]) for ring in rings for i in range(len(ring))]
    lengths = [float(np.hypot(*(b - a))) for a, b in segments]
    perimeter = sum(lengths)
    samples: list[Float2] = []
    for k in range(count):
        target = perimeter * k / count  # strictly < perimeter, so a segment always contains it
        walked = 0.0
        for (a, b), length in zip(segments, lengths):
            if walked + length >= target:
                samples.append(as_vec2(a + (target - walked) / length * (b - a)))
                break
            walked += length
    return samples


def ring_is_simple(ring: Ring) -> bool:
    """Whether ``ring`` is a simple polygon — no two non-adjacent edges cross."""
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        for j in range(i + 1, n):
            if j == i or (i == 0 and j == n - 1) or j == i + 1:
                continue  # skip shared-vertex adjacent edges
            c, d = ring[j], ring[(j + 1) % n]
            if _segments_properly_intersect(a, b, c, d):
                return False
    return True


@dataclass(frozen=True, eq=False)
class Region2Value:
    """A bounded planar area as oriented simple-polygon ``rings`` (CCW outer, CW holes; even-odd fill).

    The empty region has no rings. Equality is identity-based (``eq=False``); use
    :meth:`approx_equal` for a tolerant geometric comparison.
    """

    rings: tuple[Ring, ...]

    def __post_init__(self) -> None:
        rings = tuple(np.asarray(ring, dtype=float).reshape(-1, 2) for ring in self.rings)
        for ring in rings:
            freeze(ring)
        object.__setattr__(self, "rings", rings)

    @property
    def is_empty(self) -> bool:
        """Whether the region has no area (no rings)."""
        return len(self.rings) == 0

    def area(self) -> float:
        """The total area (outer rings minus holes); ``0`` for the empty region."""
        return abs(sum(ring_signed_area(ring) for ring in self.rings))

    def perimeter(self) -> float:
        """The total boundary length (every ring — outer and holes); ``0`` for the empty region."""
        return float(
            sum(
                float(np.hypot(*(ring[(i + 1) % len(ring)] - ring[i]))) for ring in self.rings for i in range(len(ring))
            )
        )

    def contains(self, p: Float2, tol: float = 1e-9) -> bool:
        """Whether ``p`` lies in the region (boundary included)."""
        return point_in_rings(self.rings, as_vec2(p), tol)

    def centroid(self) -> Float2:
        """The area-weighted centroid (raises ``ValueError`` for a zero-area region)."""
        total = sum(ring_signed_area(ring) for ring in self.rings)
        if total == 0.0:
            raise ValueError("the centroid of an empty region is undefined")
        acc = np.zeros(2)
        for ring in self.rings:
            centroid, area = ring_centroid_and_area(ring)
            acc += centroid * area
        return as_vec2(acc / total)

    def nearest_boundary_point(self, p: Float2) -> Float2:
        """The closest point on the region's boundary to ``p`` (raises ``ValueError`` if empty)."""
        if self.is_empty:
            raise ValueError("an empty region has no boundary")
        query = as_vec2(p)
        best_point = query
        best_sq = np.inf
        for ring in self.rings:
            n = len(ring)
            for i in range(n):
                candidate = _closest_on_segment(ring[i], ring[(i + 1) % n], query)
                sq = float(np.sum((candidate - query) ** 2))
                if sq < best_sq:
                    best_sq, best_point = sq, candidate
        return as_vec2(best_point)

    def signed_distance(self, p: Float2) -> float:
        """Distance to the boundary, **positive inside** and negative outside (raises if empty)."""
        query = as_vec2(p)
        distance = float(np.hypot(*(self.nearest_boundary_point(query) - query)))
        return distance if self.contains(query) else -distance

    def bounds(self) -> tuple[Float2, Float2]:
        """The axis-aligned ``(min_corner, max_corner)`` (raises ``ValueError`` if empty)."""
        if self.is_empty:
            raise ValueError("the bounds of an empty region are undefined")
        vertices = np.vstack(self.rings)
        return as_vec2(vertices.min(axis=0)), as_vec2(vertices.max(axis=0))

    def linearly_mapped(self, matrix: np.ndarray) -> Region2Value:
        """Every ring vertex sent through the 2×2 linear map ``matrix`` (``v ↦ matrix · v``).

        The in-chart half of a rigid 3-D transport of a ``Face`` (where ``matrix`` is the planar
        rotation relating the old and re-gauged charts). An orientation-preserving map keeps the
        rings simple and their winding, so the result is a valid region; the empty region maps to
        itself.
        """
        m = np.asarray(matrix, dtype=float)
        return Region2Value(rings=tuple(ring @ m.T for ring in self.rings))

    def approx_equal(self, other: Region2Value, atol: float = 1e-9) -> bool:
        """True if both regions have the same rings up to vertex order/rotation within ``atol``."""
        if len(self.rings) != len(other.rings):
            return False
        remaining = list(other.rings)
        for ring in self.rings:
            for i, candidate in enumerate(remaining):
                if _rings_match(ring, candidate, atol):
                    remaining.pop(i)
                    break
            else:
                return False
        return True

    def __repr__(self) -> str:
        if self.is_empty:
            return "Region2Value(empty)"
        sizes = ", ".join(str(len(ring)) for ring in self.rings)
        return f"Region2Value({len(self.rings)} ring(s): [{sizes}] vertices, area={self.area():g})"


def _rings_match(a: Ring, b: Ring, atol: float) -> bool:
    """Whether two rings are the same cycle (any rotation, same orientation) within ``atol``."""
    if len(a) != len(b):
        return False
    n = len(a)
    for shift in range(n):
        if np.allclose(a, np.roll(b, -shift, axis=0), atol=atol):
            return True
    return False
