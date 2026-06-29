# Changelog

All notable changes to fungeom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version is derived from git tags
(`vX.Y.Z`); see [RELEASING.md](RELEASING.md).

## [Unreleased]

## [0.3.0] - 2026-06-29

### Added

- **`TransformBundleSignal.resolve_over` and `TransformBundleSignal.from_matrices`.** A pose-set
  signal previously had *no* vectorized readback at all — `resolve_over` now resolves it to a dense
  `(T, N, 4, 4)` matrix stack + a `(T, N)` present mask (occluded joints `nan` / `False`), the pose
  companion to the cloud carriers. **`from_matrices(times, (T, N, 4, 4), keys, present)`** is the
  dense batch carrier (the pose-set analog of `TransformSignal.from_matrices`): it stores the raw
  `(T, N, 4, 4)` array instead of `T·N` per-frame `Transform` objects, and its `resolve_over`
  short-circuits an exact-knot grid to a straight matrix copy (bit-exact) and otherwise reads back via
  a batched per-joint quaternion slerp + a numpy translation lerp — exact-matching the per-instant
  readback at the sample instants. At T=5000, N=50, resolving onto the signal's own grid: `from_frames`
  per-instant 313 ms → `from_matrices` **~6 ms (~54×)**. Completes the retarget R1 "un-orphan the
  adapter" enablement (markers *and* poses). New shared core helper `dense_grid_brackets`.

## [0.2.3] - 2026-06-29

### Changed

- **Vectorized `Point3BundleSignal` / `ScalarBundleSignal` `resolve_over`.** The dense `(T, N, 3)` /
  `(T, N)` cloud carriers built by `from_frames` now read back in one batched numpy interpolation —
  the cloud analog of `TransformSignal.from_matrices` — instead of materializing `T·N` per-frame value
  objects. Exact knots short-circuit and an interior target is the **key-intersection** lerp of its
  bracketing frames, so the result (coordinates *and* the occlusion mask) is bit-for-bit the
  per-instant readback; any reconstruction the shortcut can't model (a `hold`/`nearest` kernel, a
  `max_gap`, an off-domain target) transparently falls back to the generic path. No API change — the
  existing `from_frames` carrier just got fast. At T=5000, N=50: same-grid 66 → ~2.7 ms (~25×), a
  between-sample grid 803 → ~2.6 ms (~300×). New shared core helper `dense_grid_readback`.

## [0.2.2] - 2026-06-27

### Fixed

- **`Face.transformed_by` / `FaceValue.transformed_by` dropped in-plane rotation.** A `Face`'s region
  lives in the plane's *normal-derived gauge* chart; a rotation **about the normal** leaves that chart
  unchanged, so the old "transport the plane, keep the region" moved only the centroid and left the
  footprint un-rotated (`static_v + (R·c − c) + t` instead of `R·static_v + t`). It now rotates the
  region by the gauge mismatch, matching the `FaceSignal` `boundary()`/`frame()` readbacks fixed in
  0.2.1. This corrects the per-instant `FaceSignal.at`/`clearance`/`contains` for any pose that spins
  the patch about its normal — previously they measured against an un-rotated footprint.

### Changed

- **Vectorized `FaceSignal.clearance` and the `PlaneSignal` accessor readbacks.** `clearance(point |
  cloud)`, `PlaneSignal.signed_distance(point | cloud)` and `plane().normal()`/`origin()` gained a
  fast `resolve_over` that applies the materialized `(T, 4, 4)` pose stack to the static geometry in
  one batched numpy op — clearance by inverse-transporting the query into the static patch frame and
  splitting the bounded distance into its out-of-plane height and in-plane overhang (the latter one
  batched GEOS call). Exact-matches the per-instant values at the sample instants, like the 0.2.1
  `boundary()`/`frame()` fix. At T=5000, K=5: `clearance` **2651 → ~30 ms (~88×)**, `signed_distance`
  142 → ~19 ms, `normal`/`origin` ~at the ~8 ms carrier. New value helper `Region2Value.linearly_mapped`.

## [0.2.1] - 2026-06-26

### Fixed

- **`FaceSignal.boundary()`/`frame()` dropped rotation** and resolved per-instant. They re-embedded
  the static 2-D region into the *transported* plane's re-gauged chart, so a rotating pose moved only
  the centroid, not the vertex offsets. Now they transport the static geometry rigidly (`R·v + t` /
  `pose ∘ static_frame`) and their `resolve_over` applies the `(T, 4, 4)` pose stack in one batched op
  (497 ms / 751 ms → ~7 / ~9 ms at T=5000). (`clearance` and `plane().signed_distance` were left
  per-instant — see Unreleased.)

## [0.2.0] - 2026-06-26

The patch *runtime* — a moving patch retarget can read off as signals, with partiality flowing end
to end.

### Added

- **`FaceSignal`** — a *moving patch*: a static `Face` fixed in a frame that moves over time
  (`FaceSignal.of(face, pose)`). Query its world geometry as signals — `plane` (→ `PlaneSignal`,
  so `normal`/`origin` follow), `frame` (→ `TransformSignal`), `boundary` (→ `Point3BundleSignal`),
  `clearance` (→ `ScalarSignal` / `ScalarBundleSignal`), `contains` (→ `BoolSignal`), `region`,
  `at(t)` (→ `Face`).
- **Rigid transport** — `Plane.transformed_by(Transform)` and `Face.transformed_by(Transform)`.
- **`Face.frame()`** (→ `Transform`, canonical patch frame) and **`Face.boundary()`**
  (→ `Point3Bundle`, footprint vertices in 3D); `Face.clearance` now also broadcasts over a
  `Point3Bundle`.
- **`TransformBundleSignal.key(j)`** (→ `TransformSignal`) — one joint's pose trajectory.
- **`TransformSignal.from_matrices(times, (T, 4, 4))`** — a vectorized batch carrier; `resolve_over`
  reads back via batched slerp + lerp (~50× faster than the per-object path, exact match).

## [0.1.0] - 2026-06-26

The first release. fungeom models geometry as an immutable, lazily-evaluated, **decidable** graph
of resolvers where partiality is first-class (`decide()` → `Resolvable` / `Unresolvable`).

### Added

- **Decidability core** — `Resolver`, `Resolvable` / `Unresolvable` (reason-carrying), `gather`,
  memoized `decide()`; `resolve()` / `is_resolvable` derived from it.
- **Geometry** — `Scalar`, `Vec2` / `Vec3`, `Direction2` / `Direction3`, `Transform` / `Transform2`,
  `Frame` / `Frame2`, `Point2` / `Point3`, and the `Plane` / `Line` / `Ray` / `Segment` family.
- **Logic** — three-valued `Bool` with strict propagation.
- **Time** — `Duration`, `Instant`, `Interval`, `Coverage`, `Sampling`, `Timeline`, `TimeMap`,
  `TimeWarp`.
- **Signals** — `Scalar` / `Vec3` / `Direction3` / `Transform` / `Point3` signals, `PlaneSignal`,
  and the three-valued `BoolSignal`; derivatives, reductions, transport, `lift`/`map`,
  `resolve_over`.
- **Collections** — `…Bundle` and `…BundleSignal` (occlusion-aware), `Roster` / `RosterMap`.
- **Regions** — `Point2Bundle`, `Region2` (general GEOS-backed boolean algebra + `offset`), `Face`.
- Ten runnable examples, full wiki + reference docs, 100% test coverage.

[Unreleased]: https://github.com/ryanrudes/fungeom/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ryanrudes/fungeom/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ryanrudes/fungeom/releases/tag/v0.1.0
