"""The instant *value*: a point on the timeline.

The phase-1 ground value is just a Python ``float`` — a number of *seconds* on
the master clock. An instant is the **affine** point space of the temporal pair
(durations are its difference space): instants subtract to a ``Duration`` and a
``Duration`` shifts an instant to another instant, but two instants do not add
(that is meaningless in an affine space). Timeline *grounding* — relating clocks
to one another the way frames relate to the world — comes in a later phase; for
now every instant lives on a single master clock. The ``Instant`` facade exposes
this value type as ``Instant.Value`` (an alias of ``float``).
"""

from __future__ import annotations


def as_instant(value: float) -> float:
    """Coerce ``value`` (e.g. a numpy float) into a plain Python ``float`` of seconds."""
    return float(value)
