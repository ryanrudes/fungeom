"""Visualizing the lazy graph — see *where* an unresolvability lives.

Because construction is lazy, a resolver *is* an expression graph, and that graph
is worth looking at. ``resolver_tree`` (or ``render_tree`` for a string) walks it
and annotates every node with its decision — green with a value if resolvable,
red with the reason if not — so a failure points you straight at the offending
sub-expression instead of a stack trace.

Run me:  python examples/04_visualizing_resolvers.py
"""

from __future__ import annotations

from rich import print as rprint

from fungeom import (
    CoordinateFrame,
    Frame,
    Point3,
    Scalar,
    Transform,
    Vec3,
    render_tree,
    resolver_tree,
)


def main() -> None:
    # 1) A fully resolvable construction: a vector scaled by another's norm.
    #    Note the Scalar (the norm) appears as its own node in the graph.
    scaled = Vec3.of(1, 2, 2).scale(Vec3.of(0, 3, 4).norm())
    print("A resolvable vector graph:\n")
    rprint(resolver_tree(scaled))

    # 2) A construction with one ungrounded part. The red ✗ propagates up from
    #    exactly the node that introduced it.
    a, b = Point3.at(0, 0, 0), Point3.at(2, 4, 6)
    loose = Point3.at(1, 1, 1, frame=CoordinateFrame.detached("gripper"))
    centroid = Point3.centroid([a, b, loose]).translate(Vec3.of(10, 0, 0))
    print("\nAn unresolvable point graph (find the ✗):\n")
    rprint(resolver_tree(centroid))

    # 3) A deferred coordinate flowing through a frame: a point placed in a
    #    still-being-built frame, with a deferred rotation angle.
    angle = Scalar.of(0.5)
    frame = Frame.world.attach("tool", Transform.rotation(Vec3.of(0, 0, 1), angle))
    point = Point3.at(Vec3.of(2, 0, 0).norm(), 0, 0, frame=frame)
    print("\nA point with deferred coordinates in a deferred frame:\n")
    rprint(resolver_tree(point))

    # `render_tree` returns the same thing as plain text (handy for logs/tests).
    assert "Vec3Norm" in render_tree(scaled)


if __name__ == "__main__":
    main()
