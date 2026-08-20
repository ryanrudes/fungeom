# Changelog

All notable changes to fungeom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version is derived from git tags
(`vX.Y.Z`); see [RELEASING.md](RELEASING.md).

## [0.8.0] - 2026-08-20

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

- **`Point3BundleSignal.hull_in(plane, tolerance=…)` → `FaceSignal`** — the general form of the
  per-frame patch: *this* cloud's convex hull, taken in *that* plane's chart, at every aligned
  instant. `fit_convex_face` is now literally `hull_in(fit_plane(t), t)`.

  It exists because one vertex set cannot answer both of a patch's questions well. *Where is the
  surface* wants a genuinely planar sample — the flat weight-bearing core of a sole — because a
  curved rim dragged into the fit tilts the plane. *How far does it extend* wants to be inclusive —
  the whole outline, rim included — because a footprint that stops at the core under-reports
  contact. Fitting the plane on one selection and hulling another is how each question gets the
  sample it needs, and until now that was expressible only for a *rigid* patch, by hand, as
  `Face.on(plane_from_A, Region2.hull(B.in_frame(plane_from_A)))`. For a deforming one there was no
  form at all: `fit_convex_face` fused the two, `FaceSignal.of` takes a *static* `Face`, and there
  is no `Region2Signal` to carry a footprint on its own.

  Built by composition — per aligned instant, `Face.on(plane.at(t), hull(cloud.at(t) in that
  chart))` — so it is time-aligned like every other two-signal op (the union of sample instants,
  clipped to the intersection of supports) and every partiality flows out of the composed resolvers
  rather than being re-implemented: an unresolvable cloud or plane (including a plane that is
  unresolvable only *between* its samples, across opposed normals), a frame with fewer than three
  present points, a wholly occluded frame, disjoint supports.

  **`tolerance` gates the hull here, not only a plane fit.** A plane supplied from outside can be
  tilted hard against the cloud and project it to a sliver, whose hull's area, centroid and boundary
  are numerical noise rather than a footprint — reachable precisely because the plane no longer
  comes from the same points. The test is the same shape as the plane fit's, and refuses
  *near*-collinear, not merely the exactly-degenerate that Qhull refuses.

### Changed

- **`FaceSignal` is now a facade** over `_TransportedFaceSignal` (the existing rigid patch, built by
  the unchanged `FaceSignal.of`) and the new `_HulledFaceSignal` (the per-frame patch behind
  `hull_in` / `fit_convex_face`). Its five batched readbacks reached past the decided value into
  `.face` / `.pose`, so each now guards on the transported kind and defers to the generic
  per-instant path otherwise — the fast paths are untouched for rigid patches.

  **`FaceSignal.region()` now decides `Unresolvable` for a per-frame patch.** It remains the static
  footprint for a transported one, so no existing use changes. A per-frame patch has no single
  static region, and returning one frame's hull as though it stood for all of them would be exactly
  the kind of plausible-but-wrong answer this library exists to refuse; ask `at(t).region()` instead.

- **`fit_convex_face` is defined as `hull_in(fit_plane(t), t)`** and no longer has a concrete of its
  own, so the fused and the general form cannot drift apart. One behavioural consequence, recorded
  because it reads like a bug and is a decision: as a two-signal op the result is reconstructed the
  way every lifted signal is — linearly, with an `undefined` boundary — where the old single-signal
  implementation inherited the source cloud's own kernel and boundary (`fit_plane` still does).

  Measured against the previous implementation rather than argued: **the samples are identical in
  every case** — same time base, same support, same fitted planes, same hulled footprints — and the
  only difference is how the patch is read *between* and *past* them, for a cloud built with a
  non-default kernel. A `via=Interpolation.hold` cloud's patch now lerps its plane between samples
  instead of selecting the earlier one, and an `outside=Boundary.hold` cloud's patch is now
  `Unresolvable` past the last sample instead of holding it. Under the default linear / `undefined`
  reading — what every consumer uses — old and new agree exactly. Re-fuse them only if a patch ever
  needs to be read with its cloud's kernel.

- **`FaceSignal.clearance`'s eager readback now runs the same kernel as its decided value**, and its
  results moved by ≤ 1.8e-15. Since 0.2.2 `resolve_over` inverse-transported the query into the
  static patch frame and split the distance into an out-of-plane height plus a batched GEOS
  overhang. That is mathematically equal to the per-instant path but a *different algorithm*, and it
  disagreed with `at(t)` by ~7e-15 relative under a moving pose while its docstring claimed to match
  it. Both now run one kernel, so the readback and the decided field are the same computation and
  agree exactly. Deliberate: one algorithm that agrees with itself beats two that agree to within a
  rounding error. Values under an identity pose are unchanged. (Removes the internal
  `_transported_clearance` / `_region_lateral_distance` helpers, and with them `signals/face.py`'s
  dependency on `shapely`.)

- **No change to what a fold means, recorded because the obvious optimization would have changed
  it.** `ScalarBundleSignal.min` / `max` / `sum` / `mean` / `count` still fold at the source's own
  sample instants and then reconstruct — *lerp-of-min*. Reducing the batched readback over a target
  grid instead is *min-of-lerp*, a different function wherever a target falls between the source's
  samples: for two members that cross, `sig.min().at(0.5)` is `0.0` while the rewrite yields `5.0`.
  The two coincide only when the target grid *is* the source's knots.
  `tests/cross_cutting/test_batched_lifts.py` pins the distinction.

### Fixed

- **A cloud authored in a non-world `frame` read back unanchored.** `Point3BundleSignal`
  world-anchors its stack at build, but the dense `resolve_over` shortcut returned the *stored*
  frame-local coordinates — so a cloud in a frame 5 units above a patch reported a clearance of
  `0.0` rather than `5.0`, while `decide()` reported it correctly. Present since the vectorized
  readback landed (0.5.0), and it survived this long because the fast path is only taken for a
  dense carrier and every test of it used the default world frame. The shortcut now anchors the
  stack before interpolating — anchor-then-lerp, which is also what keeps it bit-identical to the
  generic path — and defers to that path for an ungrounded frame. Found while unifying the
  clearance kernels: making `decide()` share the readback promoted this from a `resolve_over`-only
  wrong answer to a wrong decided value, which is how it finally showed up.

### Performance

- **A cloud measured against a carrier now answers a whole frame at once.**
  `FaceSignal.clearance(cloud)` and `PlaneSignal.signed_distance(cloud)` built one resolver **per
  member per instant** when decided, so asking for a *fold* of that field —
  `clearance(cloud).min()`, strictly less data — cost about **57×** reading the whole unreduced
  field back. The reduction was never the cost (0.5% of it): the fold simply forces `decide()`, and
  only `resolve_over` had a batched path beside it.

  The member axis is now answered in arrays, at the `decide()` level rather than in the fold's
  readback — which is why every consumer of the field got faster, not just folds:

  | 1,000 points × 281 frames | before | after | |
  | --- | --- | --- | --- |
  | `clearance(cloud).min().resolve_over(…)` | 15.34 s | 0.16 s | **96×** |
  | `clearance(cloud).at(t)` | 7.00 s | 0.15 s | **46×** |
  | the fold, against the unreduced readback | 57× | 1.5× | |

  | 6,074 points × 281 frames (1.7M point-instants) | before | after | |
  | --- | --- | --- | --- |
  | `clearance(cloud).min().resolve_over(…)` | 40.78 s | 0.74 s | **55×** |
  | the fold, against the unreduced readback | 62× | 1.7× | |

  (A fresh signal per measurement, since `decide()` memoizes.) Two independent causes, and the
  second only became visible once the first was fixed. **The lift no longer decides the cloud at
  all.** It needs three things from it — when it is sampled, where it is defined, which keys it
  declares — and was getting them by deciding it in full, which builds a `Point3Value` for every
  point of every frame: 1.7M objects, two-thirds of the remaining cost, none of them ever read
  (the coordinates arrive from the dense grid in 64 ms). A cloud is now asked for its **index**
  via `_sample_index`, which a dense carrier answers from its own `sampling` without touching a
  coordinate. The alignment rule moved to `aligned_instants`, stated against time bases rather
  than decided series, so the per-instant `decide_lifted` and the batched lift still cannot drift
  on *which* instants they answer. An index is deliberately **not** a proof of resolvability: a
  partiality only the values expose — an ungrounded frame — is reported by the grid readback
  instead, with the same reason the per-instant path gives.

  What is left is now genuinely the value representation: ~275 ms building the per-frame
  `BundleValue` dicts and ~240 ms walking `support()` over 1.7M keys in the fold, against ~250 ms
  of actual geometry. That is the struct-of-arrays floor `docs/collections.md` names, and closing
  it is a value-type design change — still not one to make under a performance report. New
  internal `decide_lifted_block` keeps `decide_lifted`'s alignment — factored out as `align_signals`
  and now shared, so the batched and per-instant lifts cannot drift on *which* instants they answer
  — and delegates each frame to a batched kernel. New batched value-type methods:
  `FaceValue.clearance_block` / `closest_point_block`, `Region2Value.contains_block` /
  `nearest_boundary_block`, `PlaneValue.to_local_block` / `embed_block`; new internal hooks
  `Point3BundleSignal._sample_index` and `_decided_grid` (the non-raising twin of `resolve_over`).

  **Every one is spelled to be bit-identical to its scalar sibling, not merely close** — the same
  cross products and `hypot` edge lengths in the even-odd test, `argmin`'s first-minimum matching
  the scalar loop's strict `<`, length-3 matrix-vector products that associate as the scalar
  `np.dot` does. Verified against the previous implementation on a **non-convex** footprint under a
  rotating-and-translating pose (an identity pose hides reassociation; a convex one hides the
  clamp): decided values, all five folds, `at(t)` and off-knot reconstruction are `array_equal`.

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
