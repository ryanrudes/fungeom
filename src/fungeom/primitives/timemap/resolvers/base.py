"""The ``TimeMap`` interface — the affine algebra of clock reparametrization.

A time map is the 1-D analog of a :class:`~fungeom.Transform`: it relates one
clock's seconds to another's by ``offset + rate · t``. You build one from a shift
(latency), a rate (playback speed), or both, and compose with ``@`` and
:meth:`inverse` exactly as transforms do. Sibling resolver types are imported
lazily to keep module load acyclic; the lower-layer ``Duration`` / ``Scalar`` are
imported normally.
"""

from __future__ import annotations

from fungeom.core.resolver import Resolver
from fungeom.primitives.duration.resolvers.base import Duration
from fungeom.primitives.scalar.resolvers.base import Scalar
from fungeom.primitives.timemap.value import AffineTimeMap


class TimeMap(Resolver[AffineTimeMap]):
    """A deferred affine clock map ``t ↦ offset + rate · t``.

    Construct one with :meth:`identity`, :meth:`shift` (a pure offset / latency),
    :meth:`rate` (a pure playback speed), :meth:`affine` (both), or :meth:`known`;
    compose with ``@`` (:meth:`compose`) and :meth:`inverse`. ``resolve()`` yields
    an :class:`~fungeom.primitives.timemap.value.AffineTimeMap` (``TimeMap.Value``).

    The one *partial* operation is :meth:`inverse`: a map with zero ``rate`` (a
    frozen clock) collapses all times to a point and cannot be inverted — it is
    :class:`~fungeom.Unresolvable`, the temporal analog of inverting a singular
    transform.
    """

    type Value = AffineTimeMap
    """The resolved value type — an :class:`AffineTimeMap`."""

    @classmethod
    def known(cls, value: AffineTimeMap) -> TimeMap:
        """Wrap an already-known :class:`AffineTimeMap` value."""
        from fungeom.primitives.timemap.resolvers.literal import LiteralTimeMap

        return LiteralTimeMap(value=value)

    @classmethod
    def identity(cls) -> TimeMap:
        """The identity map (no shift, unit rate)."""
        from fungeom.primitives.timemap.resolvers.affine import AffineTimeMapResolver

        return AffineTimeMapResolver(offset=Duration.zero, rate_factor=Scalar.of(1.0))

    @classmethod
    def shift(cls, by: Duration | float) -> TimeMap:
        """A pure offset — every time advanced by ``by`` (a latency)."""
        from fungeom.primitives.timemap.resolvers.affine import AffineTimeMapResolver

        return AffineTimeMapResolver(offset=Duration.of(by), rate_factor=Scalar.of(1.0))

    @classmethod
    def rate(cls, factor: Scalar | float) -> TimeMap:
        """A pure rate — time scaled by ``factor`` (playback speed)."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.timemap.resolvers.affine import AffineTimeMapResolver

        return AffineTimeMapResolver(offset=Duration.zero, rate_factor=as_scalar_resolver(factor))

    @classmethod
    def affine(cls, offset: Duration | float, rate: Scalar | float) -> TimeMap:
        """The general map ``offset + rate · t``."""
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.timemap.resolvers.affine import AffineTimeMapResolver

        return AffineTimeMapResolver(offset=Duration.of(offset), rate_factor=as_scalar_resolver(rate))

    @classmethod
    def aligning(cls, source: Scalar | float, target: Scalar | float) -> TimeMap:
        """The pure-offset map sending source-clock reading ``source`` to ``target``.

        The one-landmark sync: a single correspondence (a known trigger, a clap)
        fixes the offset but not the rate, so the recovered map runs at unit rate.
        Recover drift as well from two landmarks with :meth:`through`.
        """
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.timemap.resolvers.aligning import AligningTimeMap

        return AligningTimeMap(source=as_scalar_resolver(source), target=as_scalar_resolver(target))

    @classmethod
    def through(
        cls,
        first: tuple[Scalar | float, Scalar | float],
        second: tuple[Scalar | float, Scalar | float],
    ) -> TimeMap:
        """The exact affine map through two correspondences ``first`` and ``second``.

        Each correspondence is a ``(source, target)`` pair — the clapper at the start
        *and* the end. Two of them determine both offset and rate (drift).
        Unresolvable when the two source readings coincide (the rate is then
        undetermined). This is "compute the missing edge" between two clocks; feed
        the result to :meth:`Timeline.derive` to ground a detached recording.
        """
        from fungeom.primitives.scalar.resolvers.literal import as_scalar_resolver
        from fungeom.primitives.timemap.resolvers.through import ThroughTimeMap

        return ThroughTimeMap(
            source0=as_scalar_resolver(first[0]),
            target0=as_scalar_resolver(first[1]),
            source1=as_scalar_resolver(second[0]),
            target1=as_scalar_resolver(second[1]),
        )

    def compose(self, inner: TimeMap) -> TimeMap:
        """``self ∘ inner`` — apply ``inner`` first, then this map."""
        from fungeom.primitives.timemap.resolvers.composed import ComposedTimeMap

        return ComposedTimeMap(outer=self, inner=inner)

    def __matmul__(self, other: TimeMap) -> TimeMap:
        return self.compose(other)

    def inverse(self) -> TimeMap:
        """The inverse map (Unresolvable when the rate is zero)."""
        from fungeom.primitives.timemap.resolvers.inverse import InverseTimeMap

        return InverseTimeMap(timemap=self)
