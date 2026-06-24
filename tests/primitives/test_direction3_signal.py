"""Direction3Signal — the manifold stress test for the generic signal core.

The point: a value type on a *sphere* (slerp, with antipodal partiality) plugs into
the same generic core as the flat signals, and its extra partiality surfaces as an
ordinary ``Unresolvable`` — no new machinery.
"""

from __future__ import annotations

import numpy as np

from fungeom import Direction3, Direction3Signal, Instant, Interval, Sampling, Unresolvable
from fungeom.values import IntervalValue, SampledSeries


def test_slerp_interior() -> None:
    # quarter turn from +x to +y; the midpoint is the 45° unit direction
    signal = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [0, 1, 0]])
    mid = signal.at(0.5).resolve()
    assert np.allclose(mid.vector, [2**-0.5, 2**-0.5, 0.0])
    assert np.isclose(np.linalg.norm(mid.vector), 1.0)  # stays on the sphere
    assert signal.at(0.0).resolve().vector.tolist() == [1.0, 0.0, 0.0]  # exact node


def test_slerp_parallel_samples() -> None:
    # near-identical endpoints: slerp degenerates to the endpoint (no division by ~0)
    signal = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [1, 0, 0]])
    assert signal.at(0.5).resolve().vector.tolist() == [1.0, 0.0, 0.0]


def test_antipodal_is_unresolvable() -> None:
    # the crux: no unique geodesic between opposite directions
    signal = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [-1, 0, 0]])
    assert signal.is_resolvable  # the signal is well-formed...
    decision = signal.at(0.5).decide()  # ...but sampling across the antipode is not
    assert isinstance(decision, Unresolvable)
    assert "antipodal" in decision.reason


def test_at_bridges_to_direction_algebra() -> None:
    signal = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [0, 1, 0]])
    angle = signal.at(0.0).angle_to(Direction3.of(0, 1, 0)).resolve()
    assert np.isclose(angle, np.pi / 2)


def test_over_resample_and_off_domain() -> None:
    signal = Direction3Signal.from_samples([0.0, 1.0, 2.0], [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert signal.over().resolve() == IntervalValue(0.0, 2.0)
    grid = Sampling.uniform(Interval.between(Instant.at(0.0), Instant.at(2.0)), 3)
    assert isinstance(signal.resample(grid).resolve(), SampledSeries)
    assert isinstance(signal.at(9.0).decide(), Unresolvable)  # off-domain


def test_value_repr() -> None:
    signal = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [0, 1, 0]]).resolve()
    assert isinstance(signal, SampledSeries)
    assert repr(signal) == "SampledSeries(2 samples over [0, 1])"


def test_restrict_and_shift() -> None:
    sig = Direction3Signal.from_samples([0.0, 1.0, 2.0], [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    clipped = sig.restrict(Interval.between(Instant.at(0.5), Instant.at(1.5)))
    assert clipped.over().resolve() == IntervalValue(0.5, 1.5)
    assert np.isclose(np.linalg.norm(clipped.at(0.5).resolve().vector), 1.0)  # reconstructed, on the sphere
    shifted = sig.shift(2.0)
    assert shifted.over().resolve() == IntervalValue(2.0, 4.0)
    assert not sig.restrict(Interval.between(Instant.at(10.0), Instant.at(11.0))).is_resolvable


def test_zero_direction_sample_is_unresolvable() -> None:
    # a zero-vector sample has no direction -> Unresolvable (not a raise), exactly like
    # Direction3.of(0, 0, 0) -- the signal routes samples through the primitive to stay honest.
    decision = Direction3Signal.from_samples([0.0, 1.0], [[0, 0, 0], [1, 0, 0]]).decide()
    assert isinstance(decision, Unresolvable)
    # a value-count mismatch is also a build-level Unresolvable, not a crash
    mismatch = Direction3Signal.from_samples([0.0, 1.0, 2.0], [[1, 0, 0], [0, 1, 0]]).decide()
    assert isinstance(mismatch, Unresolvable)
    assert "2 values for 3 sample times" in mismatch.reason


def test_defined_at() -> None:
    sig = Direction3Signal.from_samples([0.0, 1.0, 2.0], [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert sig.defined_at(1.0).resolve() is True
    assert sig.defined_at(5.0).resolve() is False
