"""Point coercion — anywhere fungeom takes a ``Point3``, a ``SupportsPoint3`` is accepted too.

A consumer (e.g. retarget, whose markers carry a rest position) implements the structural
``__fungeom_point3__`` and passes its own symbols directly where a point is expected. These
tests pin three things:

* **transparency** — at every widened boundary, passing a marker is byte-for-byte the same as
  passing the ``Point3`` it produces;
* **the protocol + helpers** — ``isinstance`` against ``SupportsPoint3`` and the ``_as_point3`` /
  ``_as_point3s`` coercions;
* **honesty** — coercion widens the *input*, never the resolution: a marker yielding a
  ``Point3.free`` leaf stays ``Unresolvable`` until bound;

plus a **guard** that fails if any public point boundary is left as a bare ``Point3``.
"""

import inspect
import re

import pytest

from fungeom import (
    Direction3,
    Face,
    Line,
    Plane,
    Point3,
    Point3Bundle,
    Ray,
    Region2,
    Resolvable,
    Segment,
    SupportsPoint3,
    Unresolvable,
    Vec3,
)
from fungeom.primitives.point3.coercion import _as_point3, _as_point3s


class _Marker:
    """A minimal ``SupportsPoint3`` stub — stands in for a consumer's marker symbol."""

    def __init__(self, point: Point3) -> None:
        self._point = point

    def __fungeom_point3__(self) -> Point3:
        return self._point


# Distinct points used as the coerced argument(s); none coincide, so direction/normal ops resolve.
_M = Point3.at(7.0, 8.0, 9.0)
_N = Point3.at(-2.0, 3.0, 4.0)
_K = Point3.at(0.0, 5.0, 1.0)
_ON_SEG = Point3.at(3.0, 0.0, 0.0)  # lies on _SEG, so parameter_of resolves
_D = Direction3.of(1.0, 0.0, 0.0)
_U = Vec3.of(1.0, 0.0, 0.0)
_V = Vec3.of(0.0, 1.0, 0.0)

# Fixed receivers (built from real points — exercises the Point3 fast path at those boundaries too).
_PLANE = Plane.through(Point3.at(0.0, 0.0, 0.0), Direction3.of(0.0, 0.0, 1.0))
_LINE = Line.through(Point3.at(0.0, 0.0, 0.0), _D)
_RAY = Ray.through(Point3.at(0.0, 0.0, 0.0), _D)
_SEG = Segment.between(Point3.at(0.0, 0.0, 0.0), Point3.at(10.0, 0.0, 0.0))
_FACE = Face.on(_PLANE, Region2.rectangle(4.0, 2.0))
_CLOUD = Point3Bundle.of(
    [Point3.at(0.0, 0.0, 0.0), Point3.at(1.0, 1.0, 1.0), Point3.at(2.0, 0.0, 1.0)], keys=["a", "b", "c"]
)

# Every widened boundary, as ``build(mk)`` where ``mk`` maps a Point3 to a point-like.
# Markers are applied to *all* point positions, so each coercion site is exercised.
_BOUNDARIES = [
    ("Point3.centroid", lambda mk: Point3.centroid([mk(_M), mk(_N)])),
    ("Point3.affine", lambda mk: Point3.affine([mk(_M), mk(_N)], [0.4, 0.6])),
    ("Point3.lerp", lambda mk: _M.lerp(mk(_N), 0.3)),
    ("Point3.midpoint", lambda mk: _M.midpoint(mk(_N))),
    ("Point3.displacement_to", lambda mk: _M.displacement_to(mk(_N))),
    ("Point3.distance_to", lambda mk: _M.distance_to(mk(_N))),
    ("Point3.direction_to", lambda mk: _M.direction_to(mk(_N))),
    ("Point3.reflect_across", lambda mk: _M.reflect_across(mk(_N))),
    ("Line.through", lambda mk: Line.through(mk(_M), _D)),
    ("Line.through_points", lambda mk: Line.through_points(mk(_M), mk(_N))),
    ("Line.project", lambda mk: _LINE.project(mk(_M))),
    ("Line.distance_to", lambda mk: _LINE.distance_to(mk(_M))),
    ("Line.contains", lambda mk: _LINE.contains(mk(_M))),
    # points whose x increases monotonically along _LINE (the x-axis), so the orientation resolves
    (
        "Line.direction_along",
        lambda mk: _LINE.direction_along(
            [mk(Point3.at(1.0, 2.0, 0.0)), mk(Point3.at(4.0, 0.0, 3.0)), mk(Point3.at(8.0, 1.0, 0.0))]
        ),
    ),
    ("Ray.through", lambda mk: Ray.through(mk(_M), _D)),
    ("Ray.from_to", lambda mk: Ray.from_to(mk(_M), mk(_N))),
    ("Ray.project", lambda mk: _RAY.project(mk(_M))),
    ("Ray.distance_to", lambda mk: _RAY.distance_to(mk(_M))),
    ("Ray.contains", lambda mk: _RAY.contains(mk(_M))),
    ("Segment.between", lambda mk: Segment.between(mk(_M), mk(_N))),
    ("Segment.project", lambda mk: _SEG.project(mk(_M))),
    ("Segment.distance_to", lambda mk: _SEG.distance_to(mk(_M))),
    ("Segment.contains", lambda mk: _SEG.contains(mk(_M))),
    ("Segment.parameter_of", lambda mk: _SEG.parameter_of(mk(_ON_SEG))),
    ("Plane.through", lambda mk: Plane.through(mk(_M), _D)),
    ("Plane.through_points", lambda mk: Plane.through_points(mk(_M), mk(_N), mk(_K))),
    ("Plane.spanned_by", lambda mk: Plane.spanned_by(mk(_M), _U, _V)),
    ("Plane.project", lambda mk: _PLANE.project(mk(_M))),
    ("Plane.signed_distance", lambda mk: _PLANE.signed_distance(mk(_M))),
    ("Plane.contains", lambda mk: _PLANE.contains(mk(_M))),
    ("Plane.distance_to", lambda mk: _PLANE.distance_to(mk(_M))),
    ("Plane.facing", lambda mk: _PLANE.facing(mk(_M))),
    ("Plane.frame", lambda mk: _PLANE.frame(mk(_M), _D)),
    ("Plane.to_local", lambda mk: _PLANE.to_local(mk(_M))),
    ("Plane.winding_normal", lambda mk: _PLANE.winding_normal([mk(_M), mk(_N), mk(_K)])),
    ("Face.closest_point", lambda mk: _FACE.closest_point(mk(_M))),
    ("Face.clearance", lambda mk: _FACE.clearance(mk(_M))),
    ("Face.contains", lambda mk: _FACE.contains(mk(_M))),
    ("Point3Bundle.of", lambda mk: Point3Bundle.of([mk(_M), mk(_N)])),
    ("Point3Bundle.from_map", lambda mk: Point3Bundle.from_map({"a": mk(_M), "b": mk(_N)})),
    ("Point3Bundle.distances_to", lambda mk: _CLOUD.distances_to(mk(_M))),
    ("Point3Bundle.closest_point_to", lambda mk: _CLOUD.closest_point_to(mk(_M))),
    ("Point3Bundle.nearest_to", lambda mk: _CLOUD.nearest_to(mk(_M))),
]


@pytest.mark.parametrize("build", [b for _, b in _BOUNDARIES], ids=[i for i, _ in _BOUNDARIES])
def test_marker_is_transparent_at_every_boundary(build):
    """A marker resolves byte-for-byte identically to the ``Point3`` it stands for."""
    via_point = build(lambda p: p)
    via_marker = build(_Marker)
    # The coerced marker yields the *same* leaf object the point path uses, so the resolved
    # value is identical — repr is a structural, address-free comparison for these value types.
    assert repr(via_marker.resolve()) == repr(via_point.resolve())


def test_supports_point3_protocol():
    """The structural protocol matches markers and nothing accidental."""
    assert isinstance(_Marker(_M), SupportsPoint3)
    assert not isinstance(_M, SupportsPoint3)  # a Point3 has no __fungeom_point3__
    assert not isinstance(object(), SupportsPoint3)


def test_as_point3_helpers():
    """The fast path returns the Point3 unchanged; the slow path calls the dunder."""
    assert _as_point3(_M) is _M
    assert _as_point3(_Marker(_M)) is _M
    assert _as_point3s([_M, _Marker(_N)]) == [_M, _N]


def test_coercion_preserves_partiality_of_free_markers():
    """Coercion widens the input, never the resolution: a free-leaf marker stays honest.

    The substrate guarantee — a marker whose ``__fungeom_point3__`` yields a ``Point3.free``
    leaf is ``Unresolvable`` until bound, exactly as if the leaf were written by hand, and it
    surfaces through ``free_variables`` what an environment must supply.
    """

    class _FreeMarker:
        def __init__(self, key: str) -> None:
            self.key = key

        def __fungeom_point3__(self) -> Point3:
            return Point3.free(self.key)

    seg = Segment.between(_FreeMarker("p"), _FreeMarker("q"))
    assert isinstance(seg.decide(), Unresolvable)  # unbound markers — honestly undecided
    assert seg.free_variables() == frozenset({"p", "q"})  # names what must be bound
    env = {"p": Point3.at(0.0, 0.0, 0.0), "q": Point3.at(3.0, 4.0, 0.0)}
    assert isinstance(seg.decide_in(env), Resolvable)  # resolves once the env supplies both


def test_headline_authoring_over_markers_matches_rest_points():
    """The spec's headline: a patch authored over markers == the same over their rest points."""
    a = Point3.at(0.0, 0.0, 0.0)
    b = Point3.at(1.0, 0.0, 0.0)
    c = Point3.at(0.0, 1.0, 0.0)
    d = Point3.at(0.3, 0.3, 1.0)
    via_markers = Point3Bundle.of([_Marker(a), _Marker(b), _Marker(c)]).fit_plane().facing(_Marker(d))
    via_points = Point3Bundle.of([a, b, c]).fit_plane().facing(d)
    assert isinstance(via_points.decide(), Resolvable)
    assert repr(via_markers.resolve()) == repr(via_points.resolve())


def test_no_public_point_boundary_is_left_bare():
    """Guard: every public facade param mentioning ``Point3`` must also accept ``SupportsPoint3``.

    Catches a future point-accepting API that forgets to widen — the membership the spec asked
    to enforce at authoring time, encoded as a test.
    """
    facades = [Point3, Line, Ray, Plane, Segment, Face, Point3Bundle]
    bare_point3 = re.compile(r"Point3(?!Bundle|Signal|Value|\w)")
    offenders: list[str] = []
    for cls in facades:
        for name, raw in vars(cls).items():
            if isinstance(raw, (classmethod, staticmethod)):
                func = raw.__func__
            elif inspect.isfunction(raw):
                func = raw
            else:
                continue
            for param, annotation in getattr(func, "__annotations__", {}).items():
                if param == "return":
                    continue
                text = annotation if isinstance(annotation, str) else str(annotation)
                if "Callable" in text:
                    continue  # a Callable[[Point3], ...] receives a member; it is not a point input
                if bare_point3.search(text) and "SupportsPoint3" not in text:
                    offenders.append(f"{cls.__name__}.{name}({param}: {text})")
    assert not offenders, "bare Point3 params (must also accept SupportsPoint3): " + "; ".join(offenders)
