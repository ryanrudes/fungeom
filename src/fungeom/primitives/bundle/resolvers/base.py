"""The generic ``Bundle`` base — a deferred field over a nominal (entity) axis.

A bundle is the discrete counterpart of a :class:`~fungeom.primitives.signals.series.Signal`:
where a signal is a partial function of *time*, a bundle is a partial function of a
finite set of *keys*. The base carries the ops whose result type is not the facade's
own primitive — :meth:`present` (→ ``Bool``) and :meth:`count` (→ ``Scalar``) — plus
the value-type-agnostic *decide helpers* (:func:`decide_gathered` / :func:`decide_where`
/ :func:`decide_member_at`) the per-type facades delegate to (the bundle analog of the
signal layer's shared ``decide_*`` helpers). The lower-layer ``Bool`` / ``Scalar`` are
imported normally.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar


class Bundle[V](Resolver[BundleValue[V]]):
    """Generic base for the per-primitive bundle facades.

    Beyond being a ``Resolver`` of a :class:`BundleValue`, it carries the
    value-type-agnostic queries — :meth:`present` (is a key in the support?) and
    :meth:`count` (how many keys are present?) — written once. The facades add the
    ops returning their rich type (``at``, folds), the constructors that parse input,
    and delegate construction to the shared decide helpers below.
    """

    def present(self, key: Hashable) -> Bool:
        """Whether ``key`` is present in this collection (→ ``Bool``).

        The nominal-axis analog of ``Signal.defined_at``: ``False`` for a key that is
        in the roster but absent (occluded), and for a key not in the roster at all.
        """
        return _BundlePresence(bundle=self, key=key)

    def count(self) -> Scalar:
        """How many keys are present — the size of the support (→ ``Scalar``)."""
        return _BundleCount(bundle=self)


def decide_gathered[V](
    member_keys: tuple[Hashable, ...],
    members: tuple[Resolver[V], ...],
    roster: tuple[Hashable, ...],
) -> Resolvability[BundleValue[V]]:
    """Build a collection by gathering its member resolvers — strict construction.

    Unresolvable if the key/member counts differ, if keys are duplicated, or if any
    member is (so a partial member — an ungrounded point, a zero-vector direction —
    fails the whole bundle rather than being silently dropped). ``roster`` is the full
    set of declared keys (a superset of ``member_keys`` when some keys are *absent*).
    """
    if len(member_keys) != len(members):
        return Unresolvable(f"{len(members)} members for {len(member_keys)} keys")
    if len(set(member_keys)) != len(member_keys):
        return Unresolvable("duplicate keys in the bundle")
    decided: dict[Hashable, V] = {}
    for key, member in zip(member_keys, members):
        decision = member.decide()
        if isinstance(decision, Unresolvable):
            return decision
        decided[key] = decision.value
    return Resolvable(BundleValue(roster=roster, members=decided))


def decide_where[V](source: Bundle[V], keep: tuple[Hashable, ...]) -> Resolvability[BundleValue[V]]:
    """The sub-collection of ``source`` restricted to ``keep`` (roster and support both narrow)."""
    match source.decide():
        case Resolvable(collection):
            kept = set(keep)
            roster = tuple(key for key in collection.roster if key in kept)
            members = {key: value for key, value in collection.members.items() if key in kept}
            return Resolvable(BundleValue(roster=roster, members=members))
        case Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_member_at[V](bundle: Bundle[V], key: Hashable) -> Resolvability[V]:
    """The member of ``bundle`` at ``key`` — Unresolvable if absent or not in the roster."""
    match bundle.decide():
        case Resolvable(collection):
            if key not in collection.roster:
                return Unresolvable(f"key {key!r} is not in the bundle's roster")
            if not collection.present(key):
                return Unresolvable(f"key {key!r} is absent from the bundle")
            return Resolvable(collection.at(key))
        case Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BundlePresence(Bool):
    """Whether ``key`` is present in ``bundle`` — V-agnostic, written once."""

    bundle: Bundle[Any]
    key: Hashable

    def _decide(self) -> BoolDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(collection.present(self.key))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BundleCount(Scalar):
    """The number of present keys in ``bundle`` — V-agnostic, written once."""

    bundle: Bundle[Any]

    def _decide(self) -> ScalarDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(float(collection.count))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
