"""Signals — a value with a time-shaped hole, reconstructed from samples.

A ``Signal`` is a ``Resolver`` whose value is a *partial function of time*: a time
base plus samples plus a rule for reading between them. It carries *two* layers of
partiality — the signal may fail to *build* (a corrupt sampling), and a *sample*
may fall outside its domain. ``at`` bridges a signal back into the static algebra
(a ``ScalarSignal`` sampled at an instant is just a ``Scalar``); the time-axis ops
``resample`` / ``reparameterize`` / ``restrict`` / ``shift`` are themselves lazy
resolvers. One generic core serves every value type — and on a *manifold*
(directions, rotations) reconstruction is slerp, which is itself partial between
antipodal samples.

Run me:  python examples/06_signals_over_time.py
"""

from __future__ import annotations

from fungeom import Direction3Signal, Instant, Interval, Point3Signal, ScalarSignal, TimeMap


def main() -> None:
    # --- Build a scalar signal and read it --------------------------------
    speed = ScalarSignal.from_samples([0.0, 1.0, 2.0, 3.0], [0.0, 10.0, 20.0, 30.0])
    print("domain                :", speed.over().resolve())  # -> Interval [0, 3]
    print("speed at t=1.5        :", speed.at(1.5).resolve())  # linear interior -> 15.0
    print("defined at t=1.5      :", speed.defined_at(1.5).resolve())
    print("defined at t=9        :", speed.defined_at(9.0).resolve())

    # `at` bridges back into the static Scalar algebra:
    print("at(1) + at(2)         :", (speed.at(1.0) + speed.at(2.0)).resolve())

    # Sampling outside the domain has no answer (the second partiality layer).
    print("at t=9 (off-domain)   :", speed.at(9.0).decide().reason)

    # --- Time-axis transforms are lazy resolvers too ----------------------
    later = speed.shift(5.0)  # +5s latency
    print("shifted domain        :", later.over().resolve())  # -> [5, 8]
    slow = speed.reparameterize(TimeMap.rate(2.0))  # stretch time x2 (slow motion)
    print("slow-mo at t=3        :", slow.at(3.0).resolve())  # the value once at t=1.5 -> 15.0
    clip = speed.restrict(Interval.between(Instant.at(1.0), Instant.at(2.0)))
    print("restricted domain     :", clip.over().resolve())  # -> [1, 2]
    print("restricted at t=0.5   :", clip.defined_at(0.5).resolve())  # now outside -> False

    # --- Honest about gaps: a dropout is Unresolvable, not silently filled ----
    # Samples bracket a 9-second hole; max_gap=2 marks it as genuinely missing data,
    # so the signal refuses to interpolate a fictitious straight line across it.
    gappy = ScalarSignal.from_samples([0.0, 1.0, 10.0, 11.0], [0.0, 10.0, 100.0, 110.0], max_gap=2.0)
    print("support (gappy)       :", gappy.support().resolve())
    print("defined at t=0.5      :", gappy.defined_at(0.5).resolve())
    print("defined at t=5 (gap)  :", gappy.defined_at(5.0).resolve())
    print("at t=5 (gap)          :", gappy.at(5.0).decide().reason)

    # --- Signals compose: a time-aligned algebra ----
    # Two scalar signals on *different* sample bases add on the union of their
    # instants; the result is defined only where both are, and stays honest about
    # partiality (a quotient is Unresolvable where the divisor crosses zero).
    left = ScalarSignal.from_samples([0.0, 2.0], [0.0, 20.0])
    right = ScalarSignal.from_samples([0.0, 1.0, 2.0], [0.0, 10.0, 0.0])
    print("sum at t=1            :", (left + right).at(1.0).resolve())  # 10 + 10 -> 20
    crosses_zero = ScalarSignal.from_samples([0.0, 2.0], [1.0, 0.0])
    print("quotient (÷ crosses 0):", (left / crosses_zero).decide().reason)
    # cross-type lift: the distance between two *moving* points, as a ScalarSignal
    here = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [0, 0, 0]])
    there = Point3Signal.from_samples([0.0, 2.0], [[0, 0, 0], [6, 8, 0]])
    print("distance at t=1       :", here.distance_to(there).at(1.0).resolve())  # midpoint -> 5.0

    # --- On a manifold, reconstruction is slerp (and slerp is partial) ----
    heading = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [0, 1, 0]])
    print("slerp midpoint        :", heading.at(0.5).resolve().vector.round(3))  # the 45 deg direction
    # Antipodal samples have no unique geodesic -> Unresolvable, reason intact.
    flip = Direction3Signal.from_samples([0.0, 1.0], [[1, 0, 0], [-1, 0, 0]])
    print("antipodal slerp       :", flip.at(0.5).decide().reason)


if __name__ == "__main__":
    main()
