"""The generic ``Bundle`` base — a deferred field over a nominal (entity) axis.

A bundle is the discrete counterpart of a :class:`~fungeom.primitives.signals.series.Signal`:
where a signal is a partial function of *time*, a bundle is a partial function of a
finite set of *keys*. The base carries the ops whose result type is not the facade's
own primitive — :meth:`present` (→ ``Bool``) and :meth:`count` (→ ``Scalar``) —
written once here; per-type facades (``Point3Bundle``, …) add the ops that return
their rich type (``at``, ``centroid``, ``where``) and supply value parsing. The
lower-layer ``Bool`` / ``Scalar`` are imported normally.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

from fungeom.core.resolvability import Resolvable, Unresolvable
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
    ops returning their rich type and the constructors that parse input.
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
