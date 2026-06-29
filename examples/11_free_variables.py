"""Free variables — author geometry as data over late-bound leaves, bind it later.

The unknown is a *first-class leaf*. ``Point3.free(identity)`` is a point with no position yet —
``Unresolvable`` on its own — carrying an opaque, hashable ``identity``. Because it is just a leaf,
it flows through the *entire* algebra like any other point: a bundle of free points has a
``fit_plane``, that plane carries a ``Face``, and so on. So you can build a whole construction as
immutable **data** over references whose values arrive only later (think motion-capture markers),
then fill them in with ``bind(env)`` / ``resolve_in(env)``.

This is exactly the partiality model applied to a leaf — a free var is a node that is
``Unresolvable`` until you supply it — and it removes stringly-typed keys: identity is *object
identity*, so a mistyped reference is a ``NameError``, never a silent miss. It is the same patch
shape as example 09, but authored before any marker position is known.

Run me:  python examples/11_free_variables.py
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

import numpy as np

from fungeom import Face, Point3, Point3Bundle, Region2, Resolvable, Resolver, Unresolvable


@dataclass(frozen=True)
class Marker:
    """A typed symbol that *names* a marker — its object identity is the free-variable key.

    Using a real object (not a string) as the identity is the whole point: a mistyped reference
    is a ``NameError`` the type checker catches, not a key that silently fails to bind.
    """

    name: str

    def __repr__(self) -> str:
        return self.name


def show(label: str, resolver: Resolver[Any]) -> None:
    """Print whether a resolver decides — and, if not, the reason it cannot."""
    decision = resolver.decide()
    verdict = "✓ resolvable" if isinstance(decision, Resolvable) else f"✗ {decision.reason}"
    print(f"  {label:<34} {verdict}")


def sole_patch(heel: Point3, toe: Point3, mid: Point3) -> Face:
    """The contact patch under a foot, from three markers — *whatever* those points are.

    Given free points it returns a ``Face`` that is pure data over those unknowns; given concrete
    points the very same code returns a resolvable ``Face``. The footprint is the convex hull of
    the markers flattened into their own best-fit plane — the real retarget patch shape (example 09).
    """
    cloud = Point3Bundle.of([heel, toe, mid])
    plane = cloud.fit_plane()
    return Face.on(plane, Region2.hull(cloud.in_frame(plane)))


def main() -> None:
    # --- Author the patch as DATA over free markers ------------------------
    # Each marker is a typed symbol; `Point3.free` makes a point that has no value yet. `patch` is
    # a Face you can hold and pass around — built before a single position is known.
    heel, toe, mid = Marker("heel"), Marker("toe"), Marker("mid")
    patch = sole_patch(Point3.free(heel), Point3.free(toe), Point3.free(mid))

    print("The patch is data over unknowns. What does it still need?")
    print("  free_variables ->", sorted(patch.free_variables(), key=str))

    print("\nOn its own, a graph over free leaves is honestly Unresolvable:")
    show("patch.decide()", patch)

    # --- Bind the markers' positions, then the SAME graph resolves ---------
    # `env` maps each identity -> a resolver (here the marker's measured rest position). The keys are
    # the marker objects themselves; typed `Hashable` since fungeom only needs an opaque identity.
    env: dict[Hashable, Point3] = {
        heel: Point3.at(0.00, 0.00, 0.0),
        toe: Point3.at(0.28, 0.00, 0.0),
        mid: Point3.at(0.14, 0.10, 0.0),
    }
    bound_face = patch.resolve_in(env)  # bind + resolve -> a concrete FaceValue
    print("\nBound to the markers, it resolves:")
    print("  patch normal      ->", bound_face.plane.normal.round(3))
    print("  footprint corners ->", len(bound_face.region.rings[0]))

    # It resolves to EXACTLY the patch you'd get from concrete points — binding changes nothing else.
    concrete = sole_patch(Point3.at(0.00, 0.00, 0.0), Point3.at(0.28, 0.00, 0.0), Point3.at(0.14, 0.10, 0.0))
    identical = np.allclose(bound_face.region.rings[0], concrete.resolve().region.rings[0])
    print("  identical to the concrete-point patch ->", identical)

    # --- Partiality stays honest: a missing marker names itself ------------
    print("\nLeave one marker unbound -> Unresolvable, naming exactly what is missing:")
    without_mid: dict[Hashable, Point3] = {heel: env[heel], toe: env[toe]}  # `mid` absent
    missing = patch.decide_in(without_mid)
    assert isinstance(missing, Unresolvable)
    print("  decide_in (no mid) ->", missing.reason)

    # --- bind() keeps the type: a Face binds to a Face, still lazy ---------
    # When you want to keep composing instead of resolving now (e.g. hand the bound, segment-local
    # patch to a moving-frame FaceSignal), `bind` substitutes the frees and returns the same Face.
    lazy_face = patch.bind(env)
    print(
        "\nbind(env) returns a (lazy) Face:",
        isinstance(lazy_face, Face),
        "— same normal",
        lazy_face.plane().resolve().normal.round(3),
    )


if __name__ == "__main__":
    main()
