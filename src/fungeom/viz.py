"""Visualize a resolver's lazy graph, annotated with resolvability.

Because operations build an expression graph instead of computing eagerly, that
graph is worth seeing. :func:`resolver_tree` walks it via
:meth:`~fungeom.core.resolver.Resolver.children` and renders each node
with its decision — green with the value if resolvable, red with the reason if
not — so you can see *where* in a construction the unresolvability lives.
"""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Any

from fungeom.core.resolvability import Resolvable
from fungeom.core.resolver import Resolver

if TYPE_CHECKING:
    from rich.tree import Tree


def _label(resolver: Resolver[Any]) -> str:
    name = type(resolver).__name__
    decision = resolver.decide()
    if isinstance(decision, Resolvable):
        return f"[green]{name}[/] = {decision.value!r}"
    return f"[red]{name}[/] ✗ {decision.reason}"


def _build(resolver: Resolver[Any], branch: Tree) -> None:
    for child in resolver.children():
        _build(child, branch.add(_label(child)))


def resolver_tree(resolver: Resolver[Any]) -> Tree:
    """A :class:`rich.tree.Tree` of the resolver graph, annotated with decisions."""
    from rich.tree import Tree

    tree = Tree(_label(resolver))
    _build(resolver, tree)
    return tree


def render_tree(resolver: Resolver[Any]) -> str:
    """Render :func:`resolver_tree` to a plain string (handy for logs and tests)."""
    from rich.console import Console

    buffer = StringIO()
    console = Console(file=buffer, width=100, force_terminal=False)
    console.print(resolver_tree(resolver))
    return buffer.getvalue()
