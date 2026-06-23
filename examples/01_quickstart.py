"""Quickstart — construct, compose, resolve.

Every primitive is one class that you both *construct from* (classmethods like
``Point3.at`` / ``Vec3.of``) and *compose with* (fluent methods like
``a.midpoint(b)``). Composing builds an immutable, lazy graph; nothing is
computed until you call ``resolve()``.

Run me:  python examples/01_quickstart.py
"""

from __future__ import annotations

from fungeom import Point3, Vec3


def main() -> None:
    # --- Construct ---------------------------------------------------------
    # The all-numbers case is a cheap literal; you never pick a constructor
    # variant — Point3.at just does the right thing.
    a = Point3.at(0, 0, 0)
    b = Point3.at(2, 4, 6)

    # --- Compose (nothing computed yet) -----------------------------------
    midpoint = a.midpoint(b)  # -> Point3
    direction = a.direction_to(b)  # -> Direction3 (a unit vector)
    distance = a.distance_to(b)  # -> Scalar

    # --- Resolve to concrete values ---------------------------------------
    print("a, b           :", a.resolve().coord, b.resolve().coord)
    print("midpoint       :", midpoint.resolve().coord)
    print("direction (unit):", direction.resolve().vector.round(3))
    print("distance       :", round(distance.resolve(), 3))

    # --- Scalars flow across types ----------------------------------------
    # Scale a vector by *another vector's norm* — the factor is itself a
    # deferred Scalar, lifted into the graph automatically.
    scaled = Vec3.of(1, 0, 0).scale(Vec3.of(0, 3, 4).norm())  # x5
    print("scaled by norm :", scaled.resolve())

    # A point straight from deferred coordinates — no intermediate vector.
    r = Vec3.of(0, 3, 4).norm()
    p = Point3.at(r, 0.0, r / 2)
    print("point from r   :", p.resolve().coord)


if __name__ == "__main__":
    main()
