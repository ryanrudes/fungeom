"""Point clouds, and point clouds over time — collections, and the honesty of a gap.

A ``Point3Bundle`` is a *collection* of points keyed by name (a marker set): you fold
it (``centroid``), index it (``at``), mask it (an occluded marker is *absent*, not
zero), and compose two of them key-by-key (``distance_to``). Put one over time and it
is a ``Point3BundleSignal`` — a point cloud per frame on a shared clock — built by
*composition*, not a bespoke type: the generic signal core hosts a cloud as its value
once the cloud knows how to blend.

The point of this example is the **gap**. When a marker drops out mid-clip, the
library refuses to invent a position for it — sampling across the dropout is
``Unresolvable``, not a silently-interpolated fiction. ``at(t)`` slices the cloud at an
instant; its transpose ``key(k)`` slices one marker across all time (a real
``Point3Signal``), and its support gaps out *exactly* where the marker is occluded —
so ``at(t).at(k)`` and ``key(k).at(t)`` agree everywhere (the commuting square).

Run me:  python examples/08_point_clouds_over_time.py
"""

from __future__ import annotations

from fungeom import (
    Point3,
    Point3Bundle,
    Point3BundleSignal,
    Resolver,
    ScalarSignal,
    Transform,
    Unresolvable,
    Vec3,
)


def why[T](resolver: Resolver[T]) -> str:
    """The reason a resolver is Unresolvable — narrowed for the partiality prints below."""
    decision = resolver.decide()
    assert isinstance(decision, Unresolvable)
    return decision.reason


def main() -> None:
    # --- A point cloud: a keyed collection ---------------------------------
    cloud = Point3Bundle.from_map(
        {"HEAD": Point3.at(0, 0, 10), "LWRIST": Point3.at(-2, 0, 0), "RWRIST": Point3.at(2, 0, 0)}
    )
    print("count                 :", cloud.count().resolve())  # 3
    print("centroid              :", cloud.centroid().resolve().coord)  # folds over the cloud
    print("at HEAD               :", cloud.at("HEAD").resolve().coord)
    # the cloud algebra: a single transform broadcast over every point
    lifted = cloud.transformed_by(Transform.translation(Vec3.of(0, 0, 5)))
    print("HEAD lifted +5z       :", lifted.at("HEAD").resolve().coord)  # [0, 0, 15]

    # --- Masking: an occluded marker is *absent*, not zero -----------------
    # The full roster has three markers; RWRIST was not tracked this frame.
    occluded = Point3Bundle.from_map(
        {"HEAD": Point3.at(0, 0, 10), "LWRIST": Point3.at(-2, 0, 0)},
        roster=["HEAD", "LWRIST", "RWRIST"],
    )
    print("present RWRIST        :", occluded.present("RWRIST").resolve())  # False
    print("at RWRIST (occluded)  :", why(occluded.at("RWRIST")))
    print("centroid (present only):", occluded.centroid().resolve().coord)  # folds over what's there

    # --- A point cloud over time (Signal[Bundle[Point3]]) ------------------
    # HEAD slides +x; LWRIST is still; RWRIST is occluded at the middle frame.
    motion = Point3BundleSignal.from_frames(
        times=[0.0, 1.0, 2.0],
        frames=[
            [[0, 0, 10], [-2, 0, 0], [2, 0, 0]],
            [[1, 0, 10], [-2, 0, 0], [9, 9, 9]],  # RWRIST value ignored (masked off)
            [[2, 0, 10], [-2, 0, 0], [2, 0, 0]],
        ],
        keys=["HEAD", "LWRIST", "RWRIST"],
        present=[[True, True, True], [True, True, False], [True, True, True]],
    )
    # at(t) slices the whole cloud at one instant -> a Point3Bundle
    print("at t=0.5, HEAD        :", motion.at(0.5).at("HEAD").resolve().coord)  # interpolated -> [0.5, 0, 10]
    print("cloud size at t=0.5   :", motion.at(0.5).count().resolve())  # RWRIST can't be interpolated -> 2

    # The gap, made honest: RWRIST is present at t=0 and t=2 but occluded at t=1,
    # so the library refuses to invent where it was in between.
    print("at t=0.5, RWRIST      :", why(motion.at(0.5).at("RWRIST")))  # across the dropout
    print("at t=1.0, RWRIST      :", why(motion.at(1.0).at("RWRIST")))  # the exact occluded frame

    # --- distribute: one marker's trajectory over time (key = transpose of at) ---
    head = motion.key("HEAD")  # a real Point3Signal
    print("HEAD support          :", head.support().resolve())  # one unbroken span [0, 2]
    print("HEAD at t=1.5         :", head.at(1.5).resolve().coord)  # [1.5, 0, 10]

    rwrist = motion.key("RWRIST")
    print("RWRIST support (gappy):", rwrist.support().resolve())  # two point spans: present only at t=0 and t=2
    print("RWRIST at t=1.0       :", why(rwrist.at(1.0)))  # in the occlusion gap

    # Because each slice is an ordinary Point3Signal, the trajectory algebra composes:
    # the HEAD<->LWRIST separation over time is a ScalarSignal.
    separation = head.distance_to(motion.key("LWRIST"))
    print("separation is a signal:", isinstance(separation, ScalarSignal))
    print("separation at t=0,2   :", separation.at(0.0).resolve(), separation.at(2.0).resolve())


if __name__ == "__main__":
    main()
