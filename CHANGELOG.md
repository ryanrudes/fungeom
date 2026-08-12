# Changelog

All notable changes to fungeom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version is derived from git tags
(`vX.Y.Z`); see [RELEASING.md](RELEASING.md).

## [Unreleased]

### Added

- **`where(keys | Roster)` and `relabel(RosterMap)` on `Point3BundleSignal` and
  `TransformBundleSignal`** — the entity-axis ops the static bundles already had, lifted over time.
  Their absence was an asymmetry with teeth: a *selection* (a marker subset, a patch's vertices, one
  limb's joints) dropped out of its signal the moment you narrowed it, taking `fit_plane`,
  `resolve_over` and `FaceSignal` with it, so the only route was to slice the raw array before
  building the signal and give up composing afterwards.

  `where` is the entity-axis counterpart of `restrict`, which narrows *time*: entity and time are
  independent axes, so this is a narrowing rather than a rebuild — the time base, the reconstruction
  kernel and the temporal support all carry through untouched, and narrowing to nothing yields a
  valid *empty* collection rather than opening a gap. `keep` is decided **once**, not per sample, and
  a deferred `Roster` propagates. `relabel` carries a whole pose set from source-skeleton to
  target-skeleton keys at every instant — what retargeting *is* — dropping unmapped keys, carrying
  the occlusion mask across, and `Unresolvable` when the correspondence collapses two keys onto one.

  The value-level `narrowed` / `renamed` were factored out of `decide_where` / `decide_relabeled` and
  are shared with the new `decide_where_over_time` / `decide_relabeled_over_time`, so the static and
  temporal forms cannot drift apart. Concretes: `_Where…BundleSignal`, `_Relabeled…BundleSignal`.

- **`Point3BundleSignal.fit_convex_face(tolerance=…)` → `FaceSignal`** — the *bounded* companion to
  `fit_plane`, refitting the plane **and** the convex footprint to a deforming cloud at every frame.
  Bounded is the whole point: an unbounded `PlaneSignal.signed_distance` reports a foot as touching
  a floor it is two metres to the side of, while a patch's `clearance` measures to the *footprint*.
  Until now a deforming selection could be given an honest moving plane but never an honest moving
  patch — only a rigid one, via `FaceSignal.of`, which is a lie for a surface that deforms.

  **`convex` is in the name on purpose.** A hull is a modeling choice — right for a sole or a deck,
  wrong for a splayed hand whose true footprint is concave — and the membership rule forbids hiding
  such a choice behind a neutral name.

  Between samples the footprint is the earlier bracket's, on an interpolated plane: a convex hull's
  vertex count changes from frame to frame, so there is no correspondence to interpolate a footprint
  along. Values *at* sample instants are exact. Strict, like `fit_plane`: one degenerate frame makes
  the whole signal `Unresolvable`.

### Changed

- **`FaceSignal` is now a facade** over `_TransportedFaceSignal` (the existing rigid patch, built by
  the unchanged `FaceSignal.of`) and the new `_FittedFaceSignal`. Its five batched readbacks reached
  past the decided value into `.face` / `.pose`, so each now guards on the transported kind and
  defers to the generic per-instant path otherwise — the fast paths are untouched for rigid patches.

  **`FaceSignal.region()` now decides `Unresolvable` for a fitted patch.** It remains the static
  footprint for a transported one, so no existing use changes. A fitted patch has no single static
  region, and returning one frame's hull as though it stood for all of them would be exactly the
  kind of plausible-but-wrong answer this library exists to refuse; ask `at(t).region()` instead.

## [0.7.0] - 2026-08-12

### Added

- **`Sampling.at_rate(rate, count, start=0.0)`** — the grid `uniform` describes, parameterized the
  way discrete data actually arrives. A recording knows how fast it was sampled and how many samples
  it holds; it does not know the span they cover, and deriving that span means writing `count - 1` —
  one fewer interval than there are samples — at every call site. That off-by-one now lives in one
  tested place. `rate` may be a deferred `Scalar` and `start` an `Instant`, so both propagate.
  `Unresolvable` for fewer than one sample, for a rate that is not positive (zero, negative or NaN —
  none define a spacing), and for a rate so large that `1 / rate` underflows and the grid stops
  increasing. Concrete: `PacedSampling`.

## [0.5.0] - 2026-06-29

### Added

- **`Point3.coordinates_in(frame)` → `Vec3` and `Point2.coordinates_in(frame)` → `Vec2`** — the
  read-side inverse of the `in_frame` constructor: read a world-anchored point's coordinates back in
  any grounded frame. `Unresolvable` if the frame is ungrounded. Surfaced by a re-audit of `Point3`
  (the long-deferred *express-in-frame* now earns its place — `Frame` is mature, and returning the
  coordinate vector rather than a `Point3` sidesteps the world-anchoring invariant). Mirrors the
  `DisplacementVec3` cross-type pattern; kept in lockstep across `Point3` and `Point2`.

## [0.4.0] - 2026-06-29

Geometry as data — author a construction over late-bound leaves and bind it later.

### Added

- **Free-variable leaves — `Point3.free(identity)`.** A `Point3` that has no position yet:
  `Unresolvable` on its own, tagged with an opaque `Hashable` identity, and composing through the
  *entire* algebra like any other point (a bundle of free points has a `fit_plane`, that plane carries
  a `Face`, …). The unknown becomes a first-class leaf — exactly fungeom's partiality model applied to
  a leaf — so a whole construction can be authored as immutable data over late-bound references (e.g.
  motion-capture markers whose positions arrive only at bind time) instead of an imperative callable.
- **`bind` / `resolve_in` / `decide_in` / `free_variables` on `Resolver`** (so every primitive has
  them). `bind(env)` is the keystone: a **structural rewrite** that walks the immutable graph and
  substitutes each free leaf — by identity — from an `identity → resolver` environment, returning a
  *new* graph of the **same primitive type** (`Face.bind → Face`) that the ordinary `decide` /
  `resolve` machinery then evaluates unchanged. A subgraph with no (bound) frees is returned *as is*,
  so binding a fully concrete graph is a no-op (DAG sharing and the cached decision survive) and `bind`
  can be called unconditionally. `resolve_in` / `decide_in` bind then resolve / decide (`decide_in`
  names **all** still-unbound identities); `free_variables()` reports what a graph still needs.
  `decide()` / `resolve()` are **unchanged** — "resolvable as it stands?" and "resolvable *under* this
  binding?" stay two honest, distinct questions. Identity is **object identity**, so a mistyped
  reference is a `NameError`, never a silent string key.

Only `Point3.free` ships today (the motivating need); the binding machinery is generic in the core, so
a free `Scalar` / `Vec3` / `Transform` is a small future addition. See
[`docs/free-variables.md`](docs/free-variables.md).

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

[Unreleased]: https://github.com/ryanrudes/fungeom/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/ryanrudes/fungeom/compare/v0.6.0...v0.7.0
[0.5.0]: https://github.com/ryanrudes/fungeom/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/ryanrudes/fungeom/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ryanrudes/fungeom/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/ryanrudes/fungeom/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/ryanrudes/fungeom/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/ryanrudes/fungeom/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/ryanrudes/fungeom/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ryanrudes/fungeom/releases/tag/v0.1.0
