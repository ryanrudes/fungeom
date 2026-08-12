"""The generic ``Bundle`` base — a deferred field over a nominal (entity) axis.

A bundle is the discrete counterpart of a :class:`~fungeom.primitives.signals.series.Signal`:
where a signal is a partial function of *time*, a bundle is a partial function of a
finite set of *keys*. The base carries the ops whose result type is not the facade's
own primitive — :meth:`present` (→ ``Bool``), :meth:`count` (→ ``Scalar``), and
:meth:`support` (→ ``Roster``, the rung-3 identity-domain lift of the present keys) —
plus the value-type-agnostic *decide helpers* (:func:`decide_gathered` /
:func:`decide_where` / :func:`decide_member_at` / :func:`decide_relabeled`) the per-type
facades delegate to (the bundle analog of the signal layer's shared ``decide_*`` helpers).
It also carries the value-level :func:`narrowed` / :func:`renamed`, which the *signal* layer
reuses so that restricting a bundle and restricting a bundle-over-time cannot drift apart.
The lower-layer ``Bool`` / ``Scalar`` / ``Roster`` / ``RosterMap`` are imported
normally.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.core.resolver import Resolver
from fungeom.primitives.boolean.decidability import BoolDecision
from fungeom.primitives.boolean.resolvers.base import Bool
from fungeom.primitives.bundle.value import BundleValue
from fungeom.primitives.roster.decidability import RosterDecision
from fungeom.primitives.roster.resolvers.base import Roster
from fungeom.primitives.roster.value import RosterValue
from fungeom.primitives.rostermap.resolvers.base import RosterMap
from fungeom.primitives.rostermap.value import KeyCorrespondence
from fungeom.primitives.scalar.decidability import ScalarDecision
from fungeom.primitives.scalar.resolvers.base import Scalar

if TYPE_CHECKING:
    from fungeom.primitives.bundle.resolvers.boolean import BoolBundle


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

    def support(self) -> Roster:
        """The present keys, as a :class:`~fungeom.primitives.roster.resolvers.base.Roster`.

        The nominal-axis analog of ``Signal.support`` (which returns a ``Coverage``):
        the entity-axis support set, lifted from a bare key tuple into the rung-3 identity
        domain so it composes with the :meth:`~fungeom.RosterMap.source` / ``target``
        rosters of a correspondence (``RosterMap``). *Present* keys only — an absent
        (occluded) key is off the support, exactly as a temporal dropout is off a
        signal's coverage.
        """
        return _BundleSupport(bundle=self)

    def presence_mask(self) -> BoolBundle:
        """The occlusion mask as a value — each *declared* key → whether it is present (→ ``BoolBundle``).

        Total over the full roster (every declared key is in the mask, mapping to a boolean), so
        an absent (occluded) key reads as ``False`` rather than dropping out.
        """
        from fungeom.primitives.bundle.resolvers.boolean import _BundlePresenceMask

        return _BundlePresenceMask(source=self)

    def all_present(self) -> Bool:
        """Whether *every* declared key is present — no occlusions (→ ``Bool``)."""
        return _BundleAllPresent(bundle=self)

    def any_present(self) -> Bool:
        """Whether *any* declared key is present — the bundle is not wholly occluded (→ ``Bool``)."""
        return _BundleAnyPresent(bundle=self)


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


def kept_keys(keep: tuple[Hashable, ...] | Roster) -> Resolvability[frozenset[Hashable]]:
    """The key set ``keep`` names, resolving a deferred :class:`Roster` lazily.

    Split out from :func:`decide_where` so the *signal* layer can narrow a whole cloud-over-time
    against the same key set without re-deciding the roster once per sample.
    """
    if isinstance(keep, Roster):
        decided = keep.decide()
        if isinstance(decided, Unresolvable):
            return decided
        return Resolvable(frozenset(decided.value.keys))
    return Resolvable(frozenset(keep))


def narrowed[V](collection: BundleValue[V], kept: frozenset[Hashable]) -> BundleValue[V]:
    """``collection`` restricted to ``kept`` — roster and support both narrow.

    The value-level core of :func:`decide_where`, shared with the signal layer so that
    restricting a bundle and restricting a bundle *over time* cannot drift apart.
    """
    roster = tuple(key for key in collection.roster if key in kept)
    members = {key: value for key, value in collection.members.items() if key in kept}
    return BundleValue(roster=roster, members=members)


def renamed[V](collection: BundleValue[V], correspondence: KeyCorrespondence) -> BundleValue[V] | None:
    """``collection`` re-keyed through ``correspondence``, or ``None`` if two keys collapse.

    ``None`` rather than an exception: the caller turns it into an ``Unresolvable`` carrying a
    reason, which is the only shape this library reports partiality in.
    """
    keys = [key for key in collection.roster if correspondence.maps(key)]
    images = [correspondence.apply(key) for key in keys]
    if len(set(images)) != len(images):
        return None
    members = {correspondence.apply(key): collection.members[key] for key in keys if key in collection.members}
    return BundleValue(roster=tuple(images), members=members)


def decide_where[V](source: Bundle[V], keep: tuple[Hashable, ...] | Roster) -> Resolvability[BundleValue[V]]:
    """The sub-collection of ``source`` restricted to ``keep`` (roster and support both narrow).

    ``keep`` may be an explicit key tuple or a deferred :class:`Roster` (e.g. the result of
    ``values.argmin()`` / ``cloud.nearest_to(p)``) — resolved lazily, so an unresolvable roster
    propagates rather than being forced early.
    """
    decided_keep = kept_keys(keep)
    if isinstance(decided_keep, Unresolvable):
        return decided_keep
    match source.decide():
        case Resolvable(collection):
            return Resolvable(narrowed(collection, decided_keep.value))
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


def decide_zipped[U](
    a: Bundle[Any],
    b: Bundle[Any],
    combine: Callable[[Hashable], Resolver[U]],
) -> Resolvability[BundleValue[U]]:
    """Lift a pointwise op over two bundles, aligned on the *intersection* of their keys.

    A nominal axis has nothing to reconstruct a missing key from, so — unlike a
    signal, which unions sample instants — a bundle *intersects*: the result holds
    exactly the keys present in **both** operands (in the left operand's order).
    ``combine(key)`` builds the per-key combination via the ordinary static algebra
    (e.g. ``a.at(key) + b.at(key)``), so its partiality flows through — a scalar
    quotient is Unresolvable where the divisor is zero. The result is fully present
    over its intersected roster; an empty intersection is a valid empty bundle.
    """
    decided_a, decided_b = a.decide(), b.decide()
    if isinstance(decided_a, Unresolvable):
        return decided_a
    if isinstance(decided_b, Unresolvable):
        return decided_b
    shared = tuple(key for key in decided_a.value.support() if key in decided_b.value.members)
    members: dict[Hashable, U] = {}
    for key in shared:
        decision = combine(key).decide()
        if isinstance(decision, Unresolvable):
            return decision
        members[key] = decision.value
    return Resolvable(BundleValue(roster=shared, members=members))


def decide_mapped[U](
    source: Bundle[Any],
    per_key: Callable[[Hashable], Resolver[U]],
) -> Resolvability[BundleValue[U]]:
    """Map a per-member op over ``source`` (a functor/broadcast), preserving its roster.

    ``per_key(key)`` builds the mapped value via the static algebra (e.g.
    ``source.at(key).transformed_by(t)``), so per-member partiality propagates. Absent
    keys stay absent — the support (and full roster) carry through unchanged.
    """
    match source.decide():
        case Resolvable(collection):
            members: dict[Hashable, U] = {}
            for key in collection.support():
                decision = per_key(key).decide()
                if isinstance(decision, Unresolvable):
                    return decision
                members[key] = decision.value
            return Resolvable(BundleValue(roster=collection.roster, members=members))
        case Unresolvable() as bad:
            return bad
    raise AssertionError("unreachable")  # pragma: no cover


def decide_relabeled[V](source: Bundle[V], rostermap: RosterMap) -> Resolvability[BundleValue[V]]:
    """Rename ``source``'s keys through a :class:`~fungeom.RosterMap` — the identity transfer.

    The retarget seam: a bundle keyed by *source* entities (skeleton-A markers) becomes a
    bundle keyed by *target* entities (skeleton-B joints), carrying each value across the
    correspondence unchanged. A declared key outside the map's domain is **dropped** (it has
    no target — a narrowing, like :func:`decide_where`); presence/absence carries through the
    rename, so the occlusion mask transfers intact. **Unresolvable** when the correspondence
    is not injective over this roster (two declared keys mapped onto the same target collapse
    the collection) — the bundle-level mirror of ``RosterMap.inverse``'s partiality.
    """
    decided_source, decided_map = source.decide(), rostermap.decide()
    if isinstance(decided_source, Unresolvable):
        return decided_source
    if isinstance(decided_map, Unresolvable):
        return decided_map
    transferred = renamed(decided_source.value, decided_map.value)
    if transferred is None:
        return Unresolvable("relabel collapses distinct keys onto the same target")
    return Resolvable(transferred)


@dataclass(frozen=True, eq=False)
class _BundleSupport(Roster):
    """The present keys of ``bundle`` as a roster — V-agnostic, written once."""

    bundle: Bundle[Any]

    def _decide(self) -> RosterDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(RosterValue(keys=collection.support()))
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


@dataclass(frozen=True, eq=False)
class _BundleAllPresent(Bool):
    """Whether every declared key of ``bundle`` is present — V-agnostic, written once."""

    bundle: Bundle[Any]

    def _decide(self) -> BoolDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(all(collection.present(key) for key in collection.roster))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover


@dataclass(frozen=True, eq=False)
class _BundleAnyPresent(Bool):
    """Whether any declared key of ``bundle`` is present — V-agnostic, written once."""

    bundle: Bundle[Any]

    def _decide(self) -> BoolDecision:
        match self.bundle.decide():
            case Resolvable(collection):
                return Resolvable(any(collection.present(key) for key in collection.roster))
            case Unresolvable() as bad:
                return bad
        raise AssertionError("unreachable")  # pragma: no cover
