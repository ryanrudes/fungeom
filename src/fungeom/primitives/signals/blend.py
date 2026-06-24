"""The blend typeclass — how to combine two samples of a value type ``V``.

This is the *one* capability that genuinely varies between signal value types, and
the crux of the spike. For a flat space (scalars, vectors) a blend is a plain
linear interpolation and always succeeds. For a manifold (a direction, a rotation)
it is a spherical interpolation that is **partial** — antipodal endpoints have no
unique geodesic between them — so :meth:`Blend.between` returns a
:class:`~fungeom.Resolvability`, not a bare ``V``. That single choice lets a
*capability gap* (a kernel a value type cannot support there) surface as
:class:`~fungeom.Unresolvable` rather than as an inexpressible type constraint —
which is exactly how the rest of the library already handles partiality.
"""

from __future__ import annotations

from typing import Protocol

from fungeom.core.resolvability import Resolvability


class Blend[V](Protocol):
    """A way to combine two ``V`` samples at an interpolation fraction."""

    def between(self, a: V, b: V, frac: float) -> Resolvability[V]:
        """The value a fraction ``frac`` of the way from ``a`` to ``b`` (possibly partial)."""
        ...
