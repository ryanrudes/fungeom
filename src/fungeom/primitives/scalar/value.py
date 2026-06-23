"""The scalar *value*: a single real number.

The ground value is just a Python ``float``. What makes scalars first-class in
this library is not the value but the *resolvers* over it: a scale factor, an
interpolation parameter, a vector's norm, and so on are all deferred scalars, so
they live in the same expression graph as everything else. The ``Scalar`` facade
exposes this value type as ``Scalar.Value`` (an alias of ``float``).
"""

from __future__ import annotations


def as_scalar(value: float) -> float:
    """Coerce ``value`` (e.g. a numpy float) into a plain Python ``float``."""
    return float(value)
