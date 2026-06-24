"""The boolean *value*: a plain truth value.

The ground value is just a Python ``bool``. A ``Bool`` is the deferred,
*decidable* truth value — the answer to a yes/no question (a comparison, a
membership test) that may itself be unanswerable when an input cannot be
resolved. The ``Bool`` facade exposes this value type as ``Bool.Value`` (an alias
of ``bool``).
"""

from __future__ import annotations


def as_bool(value: bool) -> bool:
    """Coerce ``value`` (e.g. a numpy bool) into a plain Python ``bool``."""
    return bool(value)
