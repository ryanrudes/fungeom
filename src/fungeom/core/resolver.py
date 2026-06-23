"""The ``Resolver`` abstraction: the spine of the functional API.

A ``Resolver[T]`` is a *deferred* description of a value of type ``T``. Nothing
is computed when you build one; the value is produced only when you resolve it.
Because resolvers are immutable, every transformation (``translate``,
``reframe``, ...) returns a *new* resolver rather than mutating the existing one.
Chains of resolvers therefore form a directed acyclic graph (a lazy expression
tree) that is evaluated on demand.

The single primitive every concrete resolver implements is :meth:`_decide`, which
*proves* whether the resolver can be resolved (returning the value on success or
a reason on failure). The public :meth:`decide` memoizes it; ``resolve()`` and
``is_resolvable`` are derived from :meth:`decide`, so deciding and resolving can
never disagree, and a shared sub-graph is decided at most once.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fungeom.core.resolvability import Resolvability


class Resolver[T](ABC):
    """A generic object that can be resolved to a value of type ``T``.

    Subclasses describe *how* to produce a ``T`` and implement :meth:`_decide`.
    Resolvers are expected to be immutable value objects so that the expression
    graph they form is safe to share and cache.
    """

    @abstractmethod
    def _decide(self) -> Resolvability[T]:
        """Compute this resolver's decision. Implemented by each concrete resolver.

        Returns :class:`~fungeom.core.resolvability.Resolvable` carrying
        the computed value, or
        :class:`~fungeom.core.resolvability.Unresolvable` carrying the
        reason it cannot be resolved. Call :meth:`decide` (which memoizes this).
        """

    def decide(self) -> Resolvability[T]:
        """Prove whether this resolver can be resolved (memoized).

        The result is cached on the (immutable) resolver, so deciding it again —
        or deciding a graph that reuses it as a sub-expression — is free.
        """
        cached: Resolvability[T] | None = getattr(self, "_decision", None)
        if cached is None:
            cached = self._decide()
            object.__setattr__(self, "_decision", cached)
        return cached

    def resolve(self) -> T:
        """Resolve to a concrete value, or raise ``UnresolvableError``.

        This is total only when you already hold proof of resolvability (e.g.
        the value returned by :meth:`decide` matched as ``Resolvable``).
        """
        return self.decide().unwrap()

    @property
    def is_resolvable(self) -> bool:
        """Whether :meth:`resolve` would succeed."""
        return self.decide().ok

    def children(self) -> list[Resolver[Any]]:
        """The immediate sub-resolvers this one is built from.

        Found by inspecting dataclass fields (including those holding a tuple or
        list of resolvers), so combinators expose their structure for free —
        enough to walk or visualize the lazy graph.
        """
        field_names: dict[str, Any] | None = getattr(self, "__dataclass_fields__", None)
        if not field_names:
            return []
        found: list[Resolver[Any]] = []
        for name in field_names:
            value = getattr(self, name)
            if isinstance(value, Resolver):
                found.append(value)
            elif isinstance(value, (tuple, list)):
                found.extend(item for item in value if isinstance(item, Resolver))
        return found
