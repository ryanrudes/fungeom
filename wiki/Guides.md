# Guides

Task-oriented walkthroughs. Every example below is a **runnable, commented script** in
[`examples/`](https://github.com/ryanrudes/fungeom/tree/main/examples), exercised by the test suite
so it never drifts from the API.

## Learning path

Work top to bottom — each builds on the last.

| # | Script | The idea it teaches |
| --- | --- | --- |
| 01 | [`quickstart`](https://github.com/ryanrudes/fungeom/blob/main/examples/01_quickstart.py) | construct → compose → resolve; scalars flowing across types |
| 02 | [`coordinate_frames`](https://github.com/ryanrudes/fungeom/blob/main/examples/02_coordinate_frames.py) | a kinematic chain; grounding, and why an unplaced frame is `Unresolvable` |
| 03 | [`decidability_and_partiality`](https://github.com/ryanrudes/fungeom/blob/main/examples/03_decidability_and_partiality.py) | value-dependent partialities, reasons, propagation; predicates as `Bool` |
| 04 | [`visualizing_resolvers`](https://github.com/ryanrudes/fungeom/blob/main/examples/04_visualizing_resolvers.py) | render the lazy graph to *see* where an unresolvability lives |
| 05 | [`time_and_clocks`](https://github.com/ryanrudes/fungeom/blob/main/examples/05_time_and_clocks.py) | durations, instants, intervals & coverage with gaps |
| 06 | [`signals_over_time`](https://github.com/ryanrudes/fungeom/blob/main/examples/06_signals_over_time.py) | signals as partial functions of time; resample/reparameterize; slerp |
| 07 | [`aligning_and_warping`](https://github.com/ryanrudes/fungeom/blob/main/examples/07_aligning_and_warping.py) | recover the time map between two recordings from landmarks |
| 08 | [`point_clouds_over_time`](https://github.com/ryanrudes/fungeom/blob/main/examples/08_point_clouds_over_time.py) | a marker cloud over time — an occluded marker is honestly `Unresolvable` |
| 09 | [`regions_and_patches`](https://github.com/ryanrudes/fungeom/blob/main/examples/09_regions_and_patches.py) | the 2D region algebra, the balance margin, and a bounded-patch `Face` |
| 10 | [`contact_over_time`](https://github.com/ryanrudes/fungeom/blob/main/examples/10_contact_over_time.py) | the contact spine end-to-end; touchdown & release from marker data |

```bash
python examples/01_quickstart.py
```

## Signals over time

A signal reconstructs a value from samples and is **honest about gaps** — sampling across a dropout
is `Unresolvable`, not interpolated fiction. Build with `from_samples`/`sampled` (with
`max_gap=` to mark dropouts, `via=`/`outside=` for kernel/boundary), then `at`, `resample`,
`reparameterize` (by a `TimeMap` or monotonic `TimeWarp`), `restrict`, and derivatives
(`velocity`, `angular_velocity`). The `lift`/`map` escape hatch combines any sources per instant.
Start with example 06; deep design in
[`docs/time.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/time.md).

## Marker clouds (collections)

A `Point3Bundle` is a keyed, occlusion-aware set; a `Point3BundleSignal` is one over time. `at(t)`
gives the cloud at an instant, `key(k)` gives one marker's gappy trajectory, and the two agree on
the support (the commuting square). Folds (`centroid`), broadcasts, and key-aligned composition all
flow partiality. Start with example 08; deep design in
[`docs/collections.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/collections.md).

## Regions & contact

Build a support polygon with `Region2.hull(markers)`, read the **balance margin** off its
positive-inside `signed_distance`, and compose patches with the general boolean algebra. Lift a
region onto a `Plane` to get a `Face` — the bounded patch whose `clearance` clamps into the
footprint. Over time, the **contact spine** is:

```python
clearances = ground_cloud.fit_plane().signed_distance(foot_cloud)  # ScalarBundleSignal
contact = clearances.min().le(0.0)                                 # BoolSignal
contact.when_true().resolve()    # contact interval(s)
contact.first_true().resolve()   # touchdown
contact.last_true().resolve()    # release
```

Start with examples 09 and 10; deep design in
[`docs/regions.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/regions.md).
