"""Aligning and warping — recovering the time map between two recordings.

Synchronizing two recordings of the same event decomposes into two halves. The
hard half — *discovering* matching events from raw audio/video (cross-correlation,
DTW) — is a numerics kernel, deliberately outside this library. The other half —
*recovering the exact time map from known correspondences* (a clap, a flash, a
trigger, a hand-marked landmark) — is pure decidable algebra, and that is what
lives here.

A sync model is just a map between timelines: ``time_B = offset + rate · time_A``
is an affine ``TimeMap`` (the temporal mirror of a rigid ``Transform``); variable
drift across many landmarks is a monotonic ``TimeWarp``. One landmark fixes the
offset; two fix the drift; N fix a piecewise warp. Each is ``Unresolvable`` exactly
when the correspondences don't determine a map.

Run me:  python examples/07_aligning_and_warping.py
"""

from __future__ import annotations

from fungeom import Resolver, ScalarSignal, TimeMap, TimeWarp, Timeline, Unresolvable


def why[T](resolver: Resolver[T]) -> str:
    """The reason a resolver is Unresolvable — narrowed for the partiality prints below."""
    decision = resolver.decide()
    assert isinstance(decision, Unresolvable)
    return decision.reason


def main() -> None:
    # --- One landmark fixes the offset (a known trigger / single clap) ----
    # Camera B's clock reads 5.0s at the instant master-clock A reads 2.0s.
    offset_only = TimeMap.aligning(5.0, 2.0).resolve()
    print("aligning (offset only):", offset_only)  # offset -3, unit rate
    print("  B-time 5.0 -> A-time :", offset_only.apply(5.0))  # 2.0

    # --- Two landmarks fix offset *and* drift (clapper at start and end) ---
    # The clap (B 5.0 ↦ A 2.0) and a closing flash (B 14.95 ↦ A 12.0): the slightly
    # off rate is consumer-camera clock drift, recovered exactly.
    sync = TimeMap.through((5.0, 2.0), (14.95, 12.0))
    recovered = sync.resolve()
    print("through (offset + drift):", recovered)  # rate ~1.005
    print("  endpoints land on A   :", recovered.apply(5.0), recovered.apply(14.95))  # 2.0, 12.0

    # Two correspondences at the *same* source time leave the rate undetermined.
    print("through (same source)   :", why(TimeMap.through((5.0, 2.0), (5.0, 9.0))))

    # --- Grounding *is* synchronization: attach the detached clock ---------
    # An un-synced recording sits on a detached timeline; its instants have no
    # master-clock answer — until the recovered map grounds it.
    print("detached B at 5.0       :", why(Timeline.detached("camB").at(5.0)))
    cam_b = Timeline.master.derive("camB", by=sync)  # the recovered edge to master
    print("grounded B at 5.0 -> A  :", cam_b.at(5.0).resolve())  # 2.0s on the master clock

    # --- Many landmarks, varying drift: a monotonic TimeWarp --------------
    # When the offset isn't a single constant rate, several sync points define a
    # piecewise-linear warp (exact through the knots, not a fitted line).
    warp = TimeWarp.through([(0.0, 0.0), (5.0, 4.0), (10.0, 9.5), (15.0, 15.0)])
    print("warp at B-time 7.5      :", warp.resolve().apply(7.5))  # interpolated between knots

    # A warp must preserve order, and is defined only over its knot span.
    print("non-monotonic warp      :", why(TimeWarp.through([(0.0, 0.0), (1.0, 5.0), (0.5, 2.0)])))

    # --- Reparameterize a signal from B's clock onto the master clock -----
    sensor = ScalarSignal.from_samples([0.0, 5.0, 10.0, 15.0], [0.0, 50.0, 100.0, 150.0])
    on_master = sensor.reparameterize(warp)
    print("warped domain (A-time)  :", on_master.over().resolve())  # [0, 15] after warping
    print("sample at A-time 4.0    :", on_master.at(4.0).resolve())  # where B-time 5.0 landed -> 50.0

    # A warp invents no data past its knots — too short a warp is Unresolvable.
    short = TimeWarp.through([(0.0, 0.0), (5.0, 4.0)])  # only covers B-time [0, 5]
    print("warp too short          :", why(sensor.reparameterize(short)))


if __name__ == "__main__":
    main()
