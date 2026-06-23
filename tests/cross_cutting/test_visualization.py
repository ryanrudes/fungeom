"""The graph view: resolver_tree / render_tree."""

from __future__ import annotations

from fungeom import CoordinateFrame, Point3, Vec3, render_tree, resolver_tree


def test_render_tree_shows_values_and_reasons() -> None:
    good = Point3.at(0, 0, 0)
    bad = Point3.at(1, 1, 1, frame=CoordinateFrame.detached("gripper"))
    text = render_tree(good.midpoint(bad))
    assert "Lerp3" in text  # the combinator node
    assert "LocatedPoint3" in text  # its children
    assert "gripper" in text  # the reason surfaces at the offending node


def test_resolver_tree_walks_scalar_nodes_too() -> None:
    tree = resolver_tree(Vec3.of(1, 2, 2).scale(Vec3.of(0, 3, 4).norm()))
    # rendering the rich Tree to text should mention the derived scalar node
    assert "Vec3Norm" in render_tree(Vec3.of(0, 3, 4).norm())
    assert tree is not None
