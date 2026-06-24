"""Decidability and partiality — when geometry has no answer, you get a reason.

``decide()`` proves whether a resolver can be resolved, returning evidence:
``Resolvable`` (carrying the value) or ``Unresolvable`` (carrying a reason).
``resolve()`` and ``is_resolvable`` are just views on it. Many operations are
*partial* — undefined for particular inputs — and the library reports that as a
first-class ``Unresolvable`` rather than raising deep in a computation. Crucially,
unresolvability *propagates*: anything built on an unanswerable sub-expression is
itself unanswerable, reason intact.

Run me:  python examples/03_decidability_and_partiality.py
"""

from __future__ import annotations

from typing import Any

from fungeom import Bool, Point3, Resolvable, Resolver, Scalar, Vec3


def report(label: str, resolver: Resolver[Any]) -> None:
    """Print a one-line decision summary for any resolver."""
    decision = resolver.decide()
    if isinstance(decision, Resolvable):
        value = decision.value
        shown = getattr(value, "coord", getattr(value, "vector", value))
        print(f"  {label:<34} ✓ {shown}")
    else:
        print(f"  {label:<34} ✗ {decision.reason}")


def main() -> None:
    print("Value-dependent partialities (same op, different inputs):")
    report("1 / 2", Scalar.of(1) / Scalar.of(2))
    report("1 / 0", Scalar.of(1) / Scalar.of(0))
    report("sqrt(9)", Scalar.of(9).sqrt())
    report("sqrt(-1)", Scalar.of(-1).sqrt())
    report("normalize (0, 3, 4)", Vec3.of(0, 3, 4).normalized())
    report("normalize (0, 0, 0)", Vec3.of(0, 0, 0).normalized())

    print("\nGeometric partialities:")
    a, b = Point3.at(0, 0, 0), Point3.at(0, 0, 2)
    report("direction between two points", a.direction_to(b))
    report("direction between a point and itself", a.direction_to(a))
    report("centroid of two points", Point3.centroid([a, b]))
    report("centroid of no points", Point3.centroid([]))
    report("affine combo, weights (1, 1)", Point3.affine([a, b], [1, 1]))
    report("affine combo, weights (1, -1)", Point3.affine([a, b], [1, -1]))

    print("\nPropagation — a point built from a deferred, unanswerable coordinate:")
    # `bad` is a Scalar that cannot be resolved (distance to a detached frame).
    from fungeom import CoordinateFrame

    detached = Point3.at(1, 1, 1, frame=CoordinateFrame.detached("loose"))
    bad = a.distance_to(detached)
    report("the offending scalar itself", bad)
    report("a vector using it", Vec3.of(bad, 0, 0))
    report("a point using that vector", Point3.at(bad, 0, 0))

    print("\nPredicates are decidable truth values, too (a comparison can be Unresolvable):")
    # A comparison does not return a Python bool — it returns a deferred `Bool`,
    # because, like any resolver, it might have no answer.
    report("2 < 3", Scalar.of(2).lt(3))
    report("2 < 1", Scalar.of(2).lt(1))
    report("(unanswerable scalar) < 1", bad.lt(Scalar.of(1)))  # inherits bad's unresolvability
    # Logical algebra propagates *strictly* — there is no Kleene short-circuit, so
    # even `False and <unanswerable>` stays Unresolvable rather than collapsing to False.
    report("False and (bad < 1)", Bool.false.and_(bad.lt(Scalar.of(1))))
    report("(2 < 3) and (3 < 4)", Scalar.of(2).lt(3).and_(Scalar.of(3).lt(4)))

    print("\nRequiring proof in code — you can demand a *resolved* value:")
    decision = Point3.centroid([a, b]).decide()
    if isinstance(decision, Resolvable):
        # `decision` is statically narrowed; .value is a Point3.Value here.
        print("  centroid is proven resolvable ->", decision.value.coord)
    else:  # pragma: no cover - this branch is unreachable for this input
        print("  cannot place the part:", decision.reason)


if __name__ == "__main__":
    main()
