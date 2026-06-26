# The Primitive Layers

fungeom is a strict, acyclic stack of layers. Each primitive is one facade class; lower layers
never import higher ones. Here is the map — for the exact op-by-op surface and partiality, see the
[reference table](https://github.com/ryanrudes/fungeom/blob/main/docs/reference.md).

## Geometry

The classic kit, made decidable.

- **`Scalar`** — a real number as a node (arithmetic, `clamp`, `sign`, `mod`, comparisons → `Bool`).
- **`Vec2` / `Vec3`** — vectors (`dot`, `cross`, `norm`, `angle_to`, components → `Scalar`).
- **`Direction3` / `Direction2`** — unit vectors (a zero vector has no direction → `Unresolvable`).
- **`Transform` / `Transform2`** — rigid motion; `slerp` on SO(3)/SO(2).
- **`Frame` / `Frame2`** — coordinate frames; the **grounding** axis of partiality.
- **`Point3` / `Point2`** — framed positions; resolving world-anchors them.
- **`Plane` / `Line` / `Ray` / `Segment`** (+ 2D siblings) — the surface/curve family
  (`project`, `intersect`, `signed_distance`, `fit_plane`/`fit_line` from a cloud).

Layering: `core < scalar < vec3 < direction3 < transform < frame < point3` (2D parallel).

## Logic

- **`Bool`** — a three-valued truth value with **strict** propagation (an `Unresolvable` operand
  makes the result `Unresolvable`, not Kleene). The output type of every predicate (`Scalar.lt`,
  `Region2.contains`, …). Sits just above `core`.

## Time

The temporal family — a clean parallel to the spatial one.

- **`Duration`** (a span) / **`Instant`** (a point in time) / **`Interval`** (a range) /
  **`Coverage`** (a union of intervals — the "gappy support").
- **`Sampling`** (a time base), **`Timeline`** (a grounded clock), **`TimeMap`** (affine
  reparameterization) / **`TimeWarp`** (monotonic content warp).

Deep dive: [`docs/time.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/time.md).

## Signals — values over time

A signal is a **partial function of a clock**, reconstructed from samples, honest about gaps.

- **`ScalarSignal` / `Vec3Signal` / `Direction3Signal` / `TransformSignal` / `Point3Signal`** — one
  generic core; `at`/`resample`/`reparameterize`/`restrict`, derivatives (`velocity`,
  `angular_velocity`), reductions, `lift`/`map`.
- **`PlaneSignal`** — a moving oriented surface (fit one per frame with
  `Point3BundleSignal.fit_plane`).
- **`BoolSignal`** — a three-valued temporal predicate, born from a `ScalarSignal` threshold; reads
  its true-set off the interpolant's *exact sub-sample crossings*; `when_true`/`first_true`/
  `last_true` → the contact interval, touchdown, release.

## Collections — keyed sets, and sets over time

- **`…Bundle`** — a keyed collection (a marker set) that is **occlusion-aware**: an absent member is
  *absent*, not zero. Fold (`centroid`, `min`), broadcast, and compose two key-by-key.
- **`…BundleSignal`** — a collection *over time* (e.g. a point cloud per frame), built by
  composition — a `Signal` whose value is a `Bundle`. `at(t)` slices an instant; `key(k)` slices one
  entity's gappy trajectory.
- **`Roster` / `RosterMap`** — the entity-axis identity domain and correspondence (what retargeting
  *is* at the identity level).

Deep dive: [`docs/collections.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/collections.md).

## Regions — bounded planar areas

- **`Point2Bundle`** — a planar marker cloud (the bridge into/out of a plane's chart).
- **`Region2`** — a bounded area (the 2D sibling of `Coverage`): `hull`/`rectangle`/`disc`, a
  **general & total** boolean algebra (`union`/`intersection`/`difference`/`symmetric_difference`)
  and `offset` (via GEOS), and a **positive-inside `signed_distance`** — the balance/support margin.
- **`Face`** — a `Plane` + a `Region2`: the **bounded** contact patch, whose `clearance` clamps a
  query point *into* the footprint (right even when the foot is beside, not above).

Deep dive: [`docs/regions.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/regions.md).
