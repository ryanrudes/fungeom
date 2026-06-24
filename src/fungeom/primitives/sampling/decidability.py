"""Resolvability aliases for samplings."""

from __future__ import annotations

from fungeom.core.resolvability import Resolvability, Resolvable, Unresolvable
from fungeom.primitives.sampling.value import SamplingValue

type SamplingResolvable = Resolvable[SamplingValue]
"""A sampling decision that succeeded — carries the discrete time base."""

type SamplingUnresolvable = Unresolvable
"""A sampling decision that failed — carries the reason (e.g. out-of-order times)."""

type SamplingDecision = Resolvability[SamplingValue]
"""The result of deciding a ``Sampling``."""
