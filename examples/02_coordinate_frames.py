"""Coordinate frames — a kinematic chain, and what "grounded" buys you.

Frames attach to frames via transforms, forming a tree rooted at the world. A
point expressed in the last frame of a chain resolves all the way back to world
coordinates. The payoff of the decidability core shows up here: if any frame in
the chain is *not grounded* to the world (a part that exists but hasn't been
placed), the whole construction is ``Unresolvable`` — and the reason names the
offending frame, rather than silently producing garbage.

Run me:  python examples/02_coordinate_frames.py
"""

from __future__ import annotations

import numpy as np

from fungeom import Frame, Point3, Resolvable, Scalar, Transform, Unresolvable, Vec3


def two_link_arm(base: Frame, theta1: float, theta2: float, l1: float, l2: float) -> Point3:
    """The tool tip of a planar 2-link arm built off ``base``.

    ``base`` is a *frame resolver* — pass a grounded one (off ``Frame.world``) or
    a detached one and watch resolvability follow.
    """
    z = Vec3.of(0, 0, 1)
    shoulder = base.attach("shoulder", Transform.rotation(z, Scalar.of(theta1)))
    elbow = shoulder.attach(
        "elbow",
        # move out along the first link, then bend by theta2
        Transform.translation([l1, 0, 0]) @ Transform.rotation(z, Scalar.of(theta2)),
    )
    # the tip is l2 out along the second link
    return Point3.at(l2, 0, 0, frame=elbow)


def main() -> None:
    # --- A grounded arm resolves to world coordinates ---------------------
    tip = two_link_arm(Frame.world, theta1=0.0, theta2=0.0, l1=1.0, l2=1.0)
    print("straight arm tip :", tip.resolve().coord)  # [2, 0, 0]
    assert np.allclose(tip.resolve().coord, [2, 0, 0])

    folded = two_link_arm(Frame.world, theta1=np.pi / 2, theta2=np.pi / 2, l1=1.0, l2=1.0)
    print("folded arm tip   :", folded.resolve().coord.round(3))

    # --- The same arm on an *unplaced* base cannot be resolved ------------
    unplaced = two_link_arm(Frame.detached("unplaced_base"), 0.0, 0.0, 1.0, 1.0)
    decision = unplaced.decide()
    match decision:
        case Resolvable(point):
            print("unexpected:", point)
        case Unresolvable(reason):
            print("unplaced arm tip : Unresolvable —", reason)

    # `is_resolvable` is just the boolean view of the same decision.
    print("grounded?        :", tip.is_resolvable, "| unplaced?", unplaced.is_resolvable)

    # --- Placing the base makes the very same construction resolvable -----
    placed_base = Frame.world.attach("base", Transform.translation([10, 0, 0]))
    placed = two_link_arm(placed_base, 0.0, 0.0, 1.0, 1.0)
    print("placed arm tip   :", placed.resolve().coord)  # shifted by the base


if __name__ == "__main__":
    main()
