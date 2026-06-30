"""Coercion of point-like inputs to :class:`Point3` at fungeom's point boundaries.

Anywhere fungeom accepts a ``Point3``, it also accepts any object implementing the
structural :class:`SupportsPoint3` protocol — an object that knows how to produce a
``Point3`` via ``__fungeom_point3__``. A consumer (e.g. retarget, whose markers carry
a rest position) can then pass its *own* symbols directly where a point is expected,
and fungeom imports — and knows — nothing about that consumer.

The coercion is honest in the substrate's sense: it widens the *input* surface, never
the resolution semantics. A symbol whose ``__fungeom_point3__`` returns a
``Point3.free(...)`` leaf stays ``Unresolvable`` until bound, exactly as if the caller
had written the leaf — partiality is preserved, not papered over.

``Point3`` itself is the fast path (returned as-is); the dunder is called only for
foreign point-likes. ``_as_point3`` / ``_as_point3s`` are the single internal coercion
used at every boundary, so a future point-accepting API has one helper to route through
and cannot silently forget to coerce.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from fungeom.primitives.point3.resolvers.base import Point3


@runtime_checkable
class SupportsPoint3(Protocol):
    """Structural protocol for objects coercible to a :class:`~fungeom.Point3`.

    Implement ``__fungeom_point3__`` returning the ``Point3`` the object stands for and
    it is accepted anywhere fungeom takes a point — ``Point3Bundle.of``, ``Plane.through``,
    ``a.midpoint(b)``, and so on. Structural: nothing to subclass or import to conform, and
    ``isinstance(x, SupportsPoint3)`` is ``True`` for any object exposing the method.
    """

    def __fungeom_point3__(self) -> Point3: ...


def _as_point3(x: Point3 | SupportsPoint3) -> Point3:
    """Return ``x`` if it already is a ``Point3``, else the ``Point3`` it produces."""
    from fungeom.primitives.point3.resolvers.base import Point3

    return x if isinstance(x, Point3) else x.__fungeom_point3__()


def _as_point3s(xs: Iterable[Point3 | SupportsPoint3]) -> list[Point3]:
    """Coerce a sequence of point-likes to a list of ``Point3`` (the sequence-boundary helper)."""
    return [_as_point3(x) for x in xs]
