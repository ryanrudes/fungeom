"""Regions and patches — the 2D area algebra, the balance margin, and the bounded clearance.

A ``Region2`` is a *bounded planar area* — the 2D spatial sibling of ``Coverage`` (a union of
intervals). You build one from primitives (``rectangle`` / ``disc``) or from data (``hull`` of a
``Point2Bundle`` of markers), and compose them with a **general, total** boolean algebra
(``union`` / ``intersection`` / ``difference`` / ``symmetric_difference``) and ``offset`` (grow /
erode) — all exact on the polygon, delegated to GEOS. Its ``signed_distance`` is **positive
inside**: the balance-board / support-polygon stability margin.

Lift a region onto an oriented ``Plane`` and it becomes a ``Face`` — the *bounded* contact patch.
Unlike the infinite plane, a ``Face`` clamps a query point *into* its region, so the clearance is
honest even when the foot is *beside*, not above, the patch.

The headline retarget patch definition — ``hull(markers).offset(-d).difference(disc)`` — runs
end-to-end here: a support polygon, eroded by a safety margin, with a sore spot punched out.

Run me:  python examples/09_regions_and_patches.py
"""

from __future__ import annotations

from fungeom import (
    Direction3,
    Face,
    Plane,
    Point2,
    Point2Bundle,
    Point3,
    Point3Bundle,
    Region2,
    Resolver,
    Unresolvable,
)


def why[T](resolver: Resolver[T]) -> str:
    """The reason a resolver is Unresolvable — narrowed for the partiality prints below."""
    decision = resolver.decide()
    assert isinstance(decision, Unresolvable)
    return decision.reason


def main() -> None:
    # --- A support polygon from foot-contact markers -----------------------
    # Four contact points under a foot, keyed by name -> their convex hull is the support patch.
    contacts = Point2Bundle.from_map(
        {
            "heel": Point2.at(0.0, 0.0),
            "ball_in": Point2.at(0.2, 0.06),
            "ball_out": Point2.at(0.2, -0.06),
            "toe": Point2.at(0.28, 0.0),
        }
    )
    support = Region2.hull(contacts)
    print("support area          :", round(support.area().resolve(), 5))  # m^2
    print("support perimeter     :", round(support.perimeter().resolve(), 4))
    print("support centroid      :", support.centroid().resolve().coord.round(4))

    # --- The balance margin: signed_distance is POSITIVE inside ------------
    com = Point2.at(0.12, 0.0)  # centre of mass, projected onto the ground
    print("CoM inside support    :", support.contains(com).resolve())  # True -> balanced
    print("CoM stability margin  :", round(support.signed_distance(com).resolve(), 4))  # > 0, depth inside
    tipping = Point2.at(0.33, 0.0)  # just past the toe
    print("tipping point inside  :", support.contains(tipping).resolve())  # False
    print("tipping margin (neg)  :", round(support.signed_distance(tipping).resolve(), 4))  # < 0, outside

    # --- The headline: hull.offset(-d).difference(disc) --------------------
    # Shrink the support by a 1 cm safety margin, then punch out a sore spot under the heel.
    safe = support.offset(-0.01).difference(Region2.disc(0.02, center=(0.0, 0.0)))
    print("safe-region area      :", round(safe.area().resolve(), 5))  # smaller: eroded + holed
    print("heel now excluded     :", safe.contains(Point2.at(0.0, 0.0)).resolve())  # False (in the hole)

    # --- Region-region predicates (boundary contact counts) ----------------
    left = Region2.rectangle(0.2, 0.2, center=(0.0, 0.0))
    right = Region2.rectangle(0.2, 0.2, center=(0.2, 0.0))  # shares the x=0.1 edge
    print("feet touch (intersect):", left.intersects(right).resolve())  # True (edge contact)
    print("left contains a toe   :", left.contains_region(Region2.disc(0.01, center=(0.0, 0.0))).resolve())  # True

    # --- Lift to 3D: a Face is the BOUNDED contact patch -------------------
    # A region passed to Face.on lives in the plane's *own* 2D chart, so build it the right way:
    # take the foot markers in 3D, flatten them INTO the ground plane (in_frame), then hull.
    ground = Plane.through(Point3.at(0, 0, 0), Direction3.of(0, 0, 1))  # the z = 0 floor
    markers3d = Point3Bundle.from_map(
        {
            "heel": Point3.at(0.0, 0.0, 0.0),
            "ball_in": Point3.at(0.2, 0.06, 0.0),
            "ball_out": Point3.at(0.2, -0.06, 0.0),
            "toe": Point3.at(0.28, 0.0, 0.0),
        }
    )
    patch = Face.on(ground, Region2.hull(markers3d.in_frame(ground)))  # footprint in the plane's chart
    above = Point3.at(0.12, 0.0, 0.05)  # a foot point 5 cm above, over the footprint
    beside = Point3.at(0.6, 0.0, 0.05)  # 5 cm up but well outside the footprint
    print("clearance above       :", round(patch.clearance(above).resolve(), 4))  # ~0.05 (straight down)
    print("clearance beside      :", round(patch.clearance(beside).resolve(), 4))  # larger: clamped to the edge
    print("foot over the patch   :", patch.contains(above).resolve(), patch.contains(beside).resolve())  # True False

    # --- Partiality: an empty patch has no surface ------------------------
    empty = Face.on(ground, Region2.empty)
    print("empty-patch clearance :", why(empty.clearance(above)))  # Unresolvable, with a reason


if __name__ == "__main__":
    main()
