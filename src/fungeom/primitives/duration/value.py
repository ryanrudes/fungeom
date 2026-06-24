"""The duration *value*: a signed elapsed time.

The ground value is just a Python ``float`` — a signed number of *seconds*. A
duration is the **difference** vector space of the temporal pair: like a
``Vec3``, durations add, subtract, negate, scale, and take a ratio, but they
carry no absolute position on the timeline (that is what an ``Instant`` is). The
``Duration`` facade exposes this value type as ``Duration.Value`` (an alias of
``float``).
"""

from __future__ import annotations


def as_duration(value: float) -> float:
    """Coerce ``value`` (e.g. a numpy float) into a plain Python ``float`` of seconds."""
    return float(value)
