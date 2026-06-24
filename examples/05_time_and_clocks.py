"""Time, intervals, and clocks — the temporal layer, decidable like the rest.

Time is modeled exactly like geometry: an immutable, lazy graph of resolvers. A
``Duration`` is a *vector* (it adds and scales); an ``Instant`` is an *affine
point* on a master clock (two instants subtract to a ``Duration``, but they do not
add). Because time is totally *ordered*, it also gains spans — an ``Interval`` —
and the set of disjoint spans where data exists — a ``Coverage`` (with gaps). A
``Timeline`` is the temporal mirror of a coordinate ``Frame``: a clock only places
an instant once it is *grounded* to the master, exactly as a point only resolves
once its frame is. Comparisons (``before``, ``contains``) return a ``Bool``.

Run me:  python examples/05_time_and_clocks.py
"""

from __future__ import annotations

from fungeom import Coverage, Duration, Instant, Interval, TimeMap, Timeline, Unresolvable


def main() -> None:
    # --- Durations are vectors; instants are affine points ----------------
    lap = Duration.seconds(90)
    start = Instant.at(0.0)
    finish = start.shifted_by(lap * 2)  # instant + duration -> instant
    print("two laps end at       :", finish.resolve(), "s")
    print("elapsed (finish-start):", (finish - start).resolve(), "s")  # instant - instant -> duration
    print("start before finish   :", start.before(finish).resolve())  # a predicate -> Bool

    # --- Intervals: contiguous, ordered spans -----------------------------
    race = Interval.between(start, finish)
    print("race span             :", race.duration().resolve(), "s")
    print("t=100 within race     :", race.contains(100.0).resolve())
    print("t=500 within race     :", race.contains(500.0).resolve())

    # An interval is *partial*: a span whose end precedes its start has no value.
    backwards = Interval.between(Instant.at(10), Instant.at(0))
    print("end-before-start      :", backwards.decide().reason)

    # --- Coverage: where data actually exists (a union of disjoint spans) --
    # Two recording windows with a dropout between them.
    coverage = Coverage.of([Interval.of(Instant.at(0), 120.0), Interval.of(Instant.at(150), 90.0)])
    recorded = coverage.resolve()
    print("recorded total        :", recorded.total_duration, "s over", len(recorded.intervals), "windows")
    print("covered at t=60       :", coverage.contains(60.0).resolve())
    print("covered at t=135      :", coverage.contains(135.0).resolve())  # inside the dropout
    print("the gap               :", [(g.start, g.end) for g in coverage.gaps().resolve().intervals])

    # --- Timelines: clocks grounded to a master (the Frame/Transform mirror) ---
    # A camera clock offset 10s after the master and running at half speed.
    camera = Timeline.master.derive("camera", TimeMap.affine(Duration.seconds(10), 0.5))
    print("camera t=20 (master)  :", camera.at(20.0).resolve(), "s")  # 10 + 0.5*20 = 20

    # ...but a clock never synced to the master cannot place any instant.
    loose = Timeline.detached("handheld")
    decision = loose.at(5.0).decide()
    assert isinstance(decision, Unresolvable)
    print("un-synced clock       :", decision.reason)


if __name__ == "__main__":
    main()
