"""Unresolvability propagates through every combinator, in every input position.

This is the core promise of the decidability design: anything built on an
unanswerable sub-expression is itself unanswerable, with the reason intact. We
exercise each combinator with an ``Unresolvable`` input in each position so the
propagation branches are all covered.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from fungeom import (
    CoordinateFrame,
    Direction3,
    Frame,
    Point3,
    Scalar,
    Transform,
    Unresolvable,
    Vec2,
    Vec3,
)

# One Unresolvable and one Resolvable resolver of each type.
BAD_S, GOOD_S = Scalar.of(1) / Scalar.of(0), Scalar.of(2)
BAD_V3, GOOD_V3 = Vec3.of(0, 0, 0).normalized(), Vec3.of(1, 0, 0)
BAD_V2, GOOD_V2 = Vec2.of(0, 0).normalized(), Vec2.of(1, 0)
BAD_T, GOOD_T = Transform.rotation(Vec3.of(0, 0, 0), Scalar.of(1)), Transform.identity()
BAD_D, GOOD_D = Direction3.of(0, 0, 0), Direction3.of(1, 0, 0)
BAD_F, GOOD_F = Frame.detached("loose"), Frame.world
BAD_P = Point3.at(0, 0, 0, frame=CoordinateFrame.detached("loose"))
GOOD_P = Point3.at(0, 0, 0)

CASES: dict[str, Callable[[], object]] = {
    # scalar (both positions for binaries)
    "scalar.add.lhs": lambda: BAD_S + GOOD_S,
    "scalar.add.rhs": lambda: GOOD_S + BAD_S,
    "scalar.sub": lambda: GOOD_S - BAD_S,
    "scalar.mul.lhs": lambda: BAD_S * GOOD_S,
    "scalar.mul.rhs": lambda: GOOD_S * BAD_S,
    "scalar.div.num": lambda: BAD_S / GOOD_S,
    "scalar.div.den": lambda: GOOD_S / BAD_S,
    "scalar.min.lhs": lambda: BAD_S.min(GOOD_S),
    "scalar.min.rhs": lambda: GOOD_S.min(BAD_S),
    "scalar.max.lhs": lambda: BAD_S.max(GOOD_S),
    "scalar.max.rhs": lambda: GOOD_S.max(BAD_S),
    "scalar.pow.base": lambda: BAD_S**GOOD_S,
    "scalar.pow.exp": lambda: GOOD_S**BAD_S,
    "scalar.clamp.v": lambda: BAD_S.clamp(GOOD_S, GOOD_S),
    "scalar.clamp.lo": lambda: GOOD_S.clamp(BAD_S, GOOD_S),
    "scalar.clamp.hi": lambda: GOOD_S.clamp(GOOD_S, BAD_S),
    "scalar.abs": lambda: abs(BAD_S),
    "scalar.sqrt": lambda: BAD_S.sqrt(),
    # vec3
    "vec3.add.lhs": lambda: BAD_V3 + GOOD_V3,
    "vec3.add.rhs": lambda: GOOD_V3 + BAD_V3,
    "vec3.scale.vec": lambda: BAD_V3.scale(GOOD_S),
    "vec3.scale.factor": lambda: GOOD_V3.scale(BAD_S),
    "vec3.dot.lhs": lambda: BAD_V3.dot(GOOD_V3),
    "vec3.dot.rhs": lambda: GOOD_V3.dot(BAD_V3),
    "vec3.cross.lhs": lambda: BAD_V3.cross(GOOD_V3),
    "vec3.cross.rhs": lambda: GOOD_V3.cross(BAD_V3),
    "vec3.lerp.a": lambda: BAD_V3.lerp(GOOD_V3, GOOD_S),
    "vec3.lerp.b": lambda: GOOD_V3.lerp(BAD_V3, GOOD_S),
    "vec3.lerp.t": lambda: GOOD_V3.lerp(GOOD_V3, BAD_S),
    "vec3.proj.a": lambda: BAD_V3.project_onto(GOOD_V3),
    "vec3.proj.onto": lambda: GOOD_V3.project_onto(BAD_V3),
    "vec3.rej.a": lambda: BAD_V3.reject_from(GOOD_V3),
    "vec3.rej.onto": lambda: GOOD_V3.reject_from(BAD_V3),
    "vec3.norm": lambda: BAD_V3.norm(),
    "vec3.normalized": lambda: BAD_V3.normalized(),
    # vec2
    "vec2.add.lhs": lambda: BAD_V2 + GOOD_V2,
    "vec2.add.rhs": lambda: GOOD_V2 + BAD_V2,
    "vec2.scale.vec": lambda: BAD_V2.scale(GOOD_S),
    "vec2.scale.factor": lambda: GOOD_V2.scale(BAD_S),
    "vec2.dot.lhs": lambda: BAD_V2.dot(GOOD_V2),
    "vec2.dot.rhs": lambda: GOOD_V2.dot(BAD_V2),
    "vec2.cross.lhs": lambda: BAD_V2.cross(GOOD_V2),
    "vec2.cross.rhs": lambda: GOOD_V2.cross(BAD_V2),
    "vec2.lerp.a": lambda: BAD_V2.lerp(GOOD_V2, GOOD_S),
    "vec2.lerp.b": lambda: GOOD_V2.lerp(BAD_V2, GOOD_S),
    "vec2.lerp.t": lambda: GOOD_V2.lerp(GOOD_V2, BAD_S),
    "vec2.proj.a": lambda: BAD_V2.project_onto(GOOD_V2),
    "vec2.proj.onto": lambda: GOOD_V2.project_onto(BAD_V2),
    "vec2.rej.a": lambda: BAD_V2.reject_from(GOOD_V2),
    "vec2.rej.onto": lambda: GOOD_V2.reject_from(BAD_V2),
    "vec2.components": lambda: Vec2.of(BAD_S, GOOD_S),
    "vec2.norm": lambda: BAD_V2.norm(),
    "vec2.normalized": lambda: BAD_V2.normalized(),
    # transform
    "tf.compose.a": lambda: BAD_T @ GOOD_T,
    "tf.compose.b": lambda: GOOD_T @ BAD_T,
    "tf.inverse": lambda: BAD_T.inverse(),
    "tf.slerp.a": lambda: BAD_T.slerp(GOOD_T, GOOD_S),
    "tf.slerp.b": lambda: GOOD_T.slerp(BAD_T, GOOD_S),
    "tf.slerp.t": lambda: GOOD_T.slerp(GOOD_T, BAD_S),
    "tf.rotation.axis": lambda: Transform.rotation(BAD_V3, GOOD_S),
    "tf.rotation.angle": lambda: Transform.rotation(GOOD_V3, BAD_S),
    "tf.translation": lambda: Transform.translation(BAD_V3),
    # direction
    "dir.reversed": lambda: BAD_D.reversed(),
    "dir.angle.lhs": lambda: BAD_D.angle_to(GOOD_D),
    "dir.angle.rhs": lambda: GOOD_D.angle_to(BAD_D),
    "dir.slerp.a": lambda: BAD_D.slerp(GOOD_D, GOOD_S),
    "dir.slerp.b": lambda: GOOD_D.slerp(BAD_D, GOOD_S),
    "dir.slerp.t": lambda: GOOD_D.slerp(GOOD_D, BAD_S),
    "dir.as_vector": lambda: BAD_D.as_vector(),
    "dir.towards": lambda: Direction3.towards(BAD_V3),
    # frame
    "frame.attach.parent": lambda: BAD_F.attach("x", GOOD_T),
    "frame.attach.transform": lambda: GOOD_F.attach("x", BAD_T),
    # point
    "pt.midpoint.a": lambda: BAD_P.midpoint(GOOD_P),
    "pt.midpoint.b": lambda: GOOD_P.midpoint(BAD_P),
    "pt.lerp.t": lambda: GOOD_P.lerp(GOOD_P, BAD_S),
    "pt.disp.a": lambda: BAD_P.displacement_to(GOOD_P),
    "pt.disp.b": lambda: GOOD_P.displacement_to(BAD_P),
    "pt.translate": lambda: GOOD_P.translate(BAD_V3),
    "pt.at.coord": lambda: Point3.at(BAD_S, 0, 0),
    "pt.in_frame.local": lambda: Point3.in_frame(BAD_V3, GOOD_F),
    "pt.in_frame.frame": lambda: Point3.in_frame(GOOD_V3, BAD_F),
    "pt.centroid": lambda: Point3.centroid([GOOD_P, BAD_P]),
    "pt.affine.point": lambda: Point3.affine([GOOD_P, BAD_P], [1, 1]),
    "pt.affine.weight": lambda: Point3.affine([GOOD_P, GOOD_P], [BAD_S, GOOD_S]),
}


@pytest.mark.parametrize("thunk", CASES.values(), ids=list(CASES))
def test_unresolvability_propagates(thunk: Callable[[], object]) -> None:
    assert isinstance(thunk().decide(), Unresolvable)  # type: ignore[attr-defined]
