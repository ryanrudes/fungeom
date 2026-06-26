"""Contact over time — the spine: a moving surface, per-marker clearance, and a contact interval.

This is the capability the whole signal + bundle + region stack was built for: deciding *when a
foot is in contact with the ground*, honestly, from marker data — without ever inventing a number.

The spine, composed end to end and entirely lazy:

    ground cloud → ``fit_plane()``         a moving surface (a ``PlaneSignal``)
    ``plane.signed_distance(foot cloud)``  per-marker clearance over time (a ``ScalarBundleSignal``)
    ``.min()``                             the footprint's lowest point (a ``ScalarSignal``)
    ``.le(0)``                             "any corner touching" (a three-valued ``BoolSignal``)
    ``.when_true()`` / ``first_true`` / ``last_true``   the contact interval, touchdown, release

A ``BoolSignal`` is *three-valued*: at an instant it is true, false, or **undefined** (in a gap or
off the recording) — never silently ``False``. That is what keeps an occluded contact honest.

Run me:  python examples/10_contact_over_time.py
"""

from __future__ import annotations

from fungeom import (
    BoolSignal,
    Point3BundleSignal,
    Resolver,
    ScalarBundleSignal,
    Unresolvable,
)


def why[T](resolver: Resolver[T]) -> str:
    """The reason a resolver is Unresolvable — narrowed for the partiality prints below."""
    decision = resolver.decide()
    assert isinstance(decision, Unresolvable)
    return decision.reason


def main() -> None:
    times = [0.0, 1.0, 2.0, 3.0, 4.0]

    # --- A moving ground surface, fitted per frame -------------------------
    # Three markers on the floor (here a static z = 0 plane, but it could drift/tilt per frame).
    floor = [[[0, 0, 0], [1, 0, 0], [0, 1, 0]] for _ in times]
    ground = Point3BundleSignal.from_frames(times=times, frames=floor, keys=["g0", "g1", "g2"])
    surface = ground.fit_plane()  # a PlaneSignal — the moving patch surface

    # --- A foot descending, planting, then lifting off ---------------------
    # heel + toe heights over the clip: down at t=1, flat on the floor through t=3, lifted at t=4.
    foot = Point3BundleSignal.from_frames(
        times=times,
        frames=[
            [[0.0, 0.0, 0.20], [0.2, 0.0, 0.20]],  # t=0  both 20 cm up
            [[0.0, 0.0, 0.00], [0.2, 0.0, 0.10]],  # t=1  heel strikes
            [[0.0, 0.0, 0.00], [0.2, 0.0, 0.00]],  # t=2  flat
            [[0.0, 0.0, 0.00], [0.2, 0.0, 0.00]],  # t=3  flat
            [[0.0, 0.0, 0.20], [0.2, 0.0, 0.20]],  # t=4  lifted off
        ],
        keys=["heel", "toe"],
    )

    # --- Per-marker clearance: the plane's signed distance, broadcast over the cloud ---
    clearances = surface.signed_distance(foot)  # a ScalarBundleSignal (one clearance per marker)
    print("is a ScalarBundleSignal:", isinstance(clearances, ScalarBundleSignal))
    print("heel clearance at t=0  :", round(clearances.at(0.0).at("heel").resolve(), 3))  # 0.2 (above)
    print("heel clearance at t=2  :", round(clearances.at(2.0).at("heel").resolve(), 3))  # 0.0 (on the floor)

    # --- Fold to the footprint's lowest point, then threshold to contact ---
    lowest = clearances.min()  # a ScalarSignal: the closest-to-floor marker each instant
    contact = lowest.le(0.0)  # a BoolSignal: "any corner at or below the floor"
    print("is a BoolSignal        :", isinstance(contact, BoolSignal))

    # --- The contact interval, touchdown, and release ----------------------
    print("contact interval       :", contact.when_true().resolve())  # the planted span [1, 3]
    print("touchdown (first_true) :", contact.first_true().resolve())  # 1.0  — heel strike
    print("release   (last_true)  :", contact.last_true().resolve())  # 3.0  — toe-off

    # --- Three-valued honesty: undefined is not False ----------------------
    print("in contact at t=2.0    :", contact.at(2.0).resolve())  # True
    print("in contact at t=0.0    :", contact.at(0.0).resolve())  # False (foot is up)
    print("in contact at t=9.0    :", why(contact.at(9.0)))  # off the recording -> Unresolvable, not False

    # --- The foot's CoM track falls out of the same cloud ------------------
    com = foot.centroid()  # a Point3Signal — the marker-set centroid each instant
    print("foot CoM height at t=0 :", round(com.at(0.0).resolve().coord[2], 3))  # 0.2
    print("foot CoM height at t=2 :", round(com.at(2.0).resolve().coord[2], 3))  # 0.0


if __name__ == "__main__":
    main()
