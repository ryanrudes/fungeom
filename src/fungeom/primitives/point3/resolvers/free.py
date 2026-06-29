"""A free-variable ``Point3`` leaf — a position that has no value until bound.

The unknown made first-class: ``FreePoint3`` is a ``Point3`` resolver tagged with an
opaque, hashable ``identity`` and ``Unresolvable`` on its own. It is *exactly* fungeom's
partiality model applied to a leaf — a point that cannot answer yet — so it composes
through the whole algebra like any other ``Point3`` (a bundle of free points has a
``fit_plane``, that plane has a ``Face``, …). :meth:`~fungeom.core.resolver.Resolver.bind`
substitutes it from an ``identity -> resolver`` environment, and the result resolves
through the ordinary machinery. This is the leaf that lets a whole geometric construction
be authored as data over late-bound references (e.g. motion-capture markers whose
positions arrive only at bind time) rather than as an imperative callable.
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from typing import Any

from fungeom.core.resolvability import Unresolvable
from fungeom.core.resolver import Resolver
from fungeom.primitives.point3.decidability import Point3Decision
from fungeom.primitives.point3.resolvers.base import Point3


@dataclass(frozen=True, eq=False)
class FreePoint3(Point3):
    """A late-bound point identified by ``identity`` — ``Unresolvable`` until bound.

    On its own it cannot resolve (criterion: a construction with unbound markers
    genuinely has no value). :meth:`~fungeom.core.resolver.Resolver.bind` replaces it,
    by ``identity``, with the resolver supplied in the environment; the identity is an
    opaque :class:`~collections.abc.Hashable` (the consumer may use the referenced
    object itself as the key), so nothing here is stringly-typed.
    """

    identity: Hashable

    def _decide(self) -> Point3Decision:
        return Unresolvable(f"free variable {self.identity!r} is unbound")

    def _substitute(self, env: Mapping[Hashable, Resolver[Any]], memo: dict[int, Resolver[Any]]) -> Resolver[Any]:
        if self.identity in env:
            return env[self.identity]
        return self

    def free_variables(self) -> frozenset[Hashable]:
        return frozenset((self.identity,))
