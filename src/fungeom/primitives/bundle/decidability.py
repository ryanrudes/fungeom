"""Resolvability aliases for bundles."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.bundle.value import BundleValue

type BundleResolvable[V] = Resolvable[BundleValue[V]]
"""A bundle decision that succeeded — carries the keyed collection."""

type BundleUnresolvable = Unresolvable
"""A bundle decision that failed — carries the reason."""

type BundleDecision[V] = Resolvability[BundleValue[V]]
"""The result of deciding a ``Bundle``."""
