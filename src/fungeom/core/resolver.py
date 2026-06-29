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
from collections.abc import Hashable, Mapping
from dataclasses import replace
from typing import Any, Self, cast

from fungeom.core.resolvability import Resolvability, Unresolvable


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

    # -- Free variables: late-bound leaves and binding ---------------------------------
    #
    # A *free variable* is a leaf that carries an opaque, hashable identity and is
    # ``Unresolvable`` on its own (see ``Point3.free``). Because it is just a leaf, it
    # composes through the whole algebra exactly like any other resolver; binding is a
    # purely *structural* rewrite of the immutable graph (no env is threaded through
    # ``decide``), so everything downstream — ``decide`` / ``resolve`` and their
    # memoization — is untouched. ``decide()`` keeps its meaning: a graph with unbound
    # frees genuinely *is* unresolvable as it stands; ``decide_in`` answers the distinct
    # question "is it resolvable *under* this binding?".

    def bind(self, env: Mapping[Hashable, Resolver[Any]]) -> Self:
        """Substitute free-variable leaves from ``env``, returning a bound graph.

        Walks this immutable graph and replaces each free leaf (see ``Point3.free``)
        whose ``identity`` is a key of ``env`` with the bound resolver, leaving every
        other node untouched — a structural rewrite that yields a *new* graph the
        ordinary :meth:`decide` / :meth:`resolve` machinery then evaluates unchanged.
        A subgraph with no (bound) free leaves is returned **as is**, so binding a
        fully concrete graph is a no-op — DAG sharing and the cached decision are
        preserved, and you may call ``bind`` unconditionally without first consulting
        :meth:`free_variables`. Unbound frees stay free: the result is still a valid,
        ``Unresolvable`` resolver that names them.
        """
        return cast("Self", self._substitute(env, {}))

    def decide_in(self, env: Mapping[Hashable, Resolver[Any]]) -> Resolvability[T]:
        """Prove whether this graph resolves *under* the binding ``env``.

        The env-aware counterpart to :meth:`decide` (which is left unchanged — a graph
        with unbound frees genuinely is ``Unresolvable`` on its own). Binds via
        :meth:`bind`, then: if any free is still unbound, returns one ``Unresolvable``
        **naming all** of them; otherwise returns the bound graph's ordinary (memoized)
        decision. Resolving and deciding under an env can therefore never disagree.
        """
        bound = self.bind(env)
        unbound = bound.free_variables()
        if unbound:
            names = ", ".join(sorted(repr(identity) for identity in unbound))
            return Unresolvable(f"free variables unbound: {names}")
        return bound.decide()

    def resolve_in(self, env: Mapping[Hashable, Resolver[Any]]) -> T:
        """Resolve this graph under ``env`` — :meth:`bind`, then resolve.

        Sugar for ``decide_in(env).unwrap()``: returns the value once every reachable
        free is bound (and the graph resolves), else raises ``UnresolvableError`` whose
        reason names the still-unbound frees.
        """
        return self.decide_in(env).unwrap()

    def free_variables(self) -> frozenset[Hashable]:
        """The identities of every free-variable leaf reachable from this graph.

        Empty for a fully concrete graph. A free leaf contributes its own identity;
        every other node is the union over its :meth:`children`. Lets a consumer ask
        *what a graph still needs* before binding — and backs :meth:`decide_in`'s
        missing-variable report.
        """
        free: set[Hashable] = set()
        for child in self.children():
            free |= child.free_variables()
        return frozenset(free)

    def _substitute(self, env: Mapping[Hashable, Resolver[Any]], memo: dict[int, Resolver[Any]]) -> Resolver[Any]:
        """Rebuild this node with free leaves bound from ``env`` (the worker for :meth:`bind`).

        Recurses into the resolver-typed dataclass fields (including a tuple or list of
        resolvers) and rebuilds this node via :func:`dataclasses.replace` only if a child
        actually changed — otherwise returns ``self``, so an unaffected subgraph keeps its
        identity, sharing, and cached decision. ``memo`` keys on ``id`` so a shared
        sub-graph is substituted once and stays shared. A free leaf overrides this to look
        itself up in ``env``.
        """
        cached = memo.get(id(self))
        if cached is not None:
            return cached
        field_names: dict[str, Any] | None = getattr(self, "__dataclass_fields__", None)
        changes: dict[str, Any] = {}
        for name in field_names or {}:
            value = getattr(self, name)
            if isinstance(value, Resolver):
                replaced = value._substitute(env, memo)
                if replaced is not value:
                    changes[name] = replaced
            elif isinstance(value, (tuple, list)):
                items = [item._substitute(env, memo) if isinstance(item, Resolver) else item for item in value]
                if any(new is not old for new, old in zip(items, value)):
                    changes[name] = type(value)(items)
        # ``self`` is statically the abstract ``Resolver`` (not a dataclass), but we only reach
        # ``replace`` when it has ``__dataclass_fields__`` — cast past the stub's dataclass bound.
        result: Resolver[Any] = replace(cast(Any, self), **changes) if changes else self
        memo[id(self)] = result
        return result
