# Collections in fungeom

A design note for adding **plurality** to the library — a collection of things
(a point cloud), and a collection of things over time (a point cloud over time).
It is a plan, not yet built: read [`README.md`](../README.md) for the decidability
core and [`time.md`](time.md) for the temporal layer first — this note assumes both
(`decide()`, `Resolvable`/`Unresolvable`, facade-over-concrete-resolvers,
`<Primitive>.Value`, `Signal[V]`/`SampledSeries[V]`/`Blend[V]`, `Coverage` support)
and is built almost entirely by mirroring them one axis over.

---

## The spine: plurality is the third structural axis

A geometric datum factors into an **inner value `V`** — the geometry itself, a
coordinate `(3,)` or a rotation `(3,3)` — carried over zero or more **outer axes**:
indices you can enumerate, each carrying its own *support* (where the datum is
defined along that axis).

```
        outer axes  (indexable, each with support)        inner value V
( T,        N,        … )                            ×    (3,) | (3,3) | …
  │          │                                              └ geometry: Point3 / Transform / …
  │          └ entity axis  (nominal)   → a collection  (Bundle)
  └ time axis (metric)      → a signal             (Signal)
```

Space lives *inside* `V`. **Time and plurality are outer axes.** A "field" is `V`
indexed over a product of outer axes:

- `Signal[V]` — a field over `{time}`.
- `Bundle[V]` — a field over `{entity}`. **(new)**
- `Signal[Bundle[V]]` — a field over `{time, entity}` — a collection over time.

This is the load-bearing claim: a collection and a collection-over-time are *not*
two new types. They are the **one** field constructor with one vs two outer axes,
and `Signal[Bundle[V]]` falls out of the *existing* signal core because that core is
fully `V`-agnostic (`SampledSeries[V]` holds `values: tuple[V, …]` + a `Blend[V]`;
it never inspects `V`). We build `Bundle`; over-time is composition.

---

## A collection is a field over a *nominal* axis

A `Signal` is a partial function `Time ⇀ V`. A `Bundle` is a partial function
`Entities ⇀ V`. Same constructor; the only thing that differs is the **structure of
the index axis**:

| Axis kind | Example | Ordered | Metric | Reconstruction | Support is |
| --- | --- | :-: | :-: | --- | --- |
| **nominal** | markers, entities | no | no | **none** (exact only) | a key-set |
| **metric / continuous** | time, arc-length | yes | yes | interpolation (`Blend`) | a `Coverage` (intervals) |

`Signal` already implements the **metric** axis. **`Bundle` is the *nominal*-axis
instantiation of the same field abstraction.** (A third instantiation lurks but is
out of scope: a *path / polyline* is a metric axis whose parameter is spatial
arc-length — "a signal over space" — which is why the field core should treat
"metric axis" and "nominal axis" as the pluggable thing, and Signal built the first
one. We do **not** chase paths here.)

---

## Support is first-class — which dissolves "strict vs masked"

The tempting fork — does one unresolvable element (an occluded marker) kill the
whole collection (strict, like `gather`) or not (masked)? — is a false choice, for
the same reason it was a false choice for signals. **Every collection carries a
total `support` (the present keys), defaulting to the full index**, exactly as every
signal carries a `Coverage` defaulting to its hull. Then:

- a *complete* cloud has `support == index`;
- a *masked* cloud (occlusion) has `support ⊊ index`;
- **"strict" is a query-time demand, not a type.**

Operations classify by how they treat support:

| Op class | Example | Support behavior | Partiality |
| --- | --- | --- | --- |
| preserving (functor `map`) | `cloud.transformed_by(T)` | output = input | propagates |
| broadcast (applicative) | `cloud.transformed_by(one T)` | input | propagates |
| intersecting (`zip` / lift₂) | `a.displacement_to(b)` | `A.support ∩ B.support` **by key** | disjoint → `Unresolvable` |
| collapsing (fold) | `centroid()`, `count()` | → a single primitive | empty support → `Unresolvable` |
| narrowing (filter) | `where(keys)` | shrinks support | — |
| **completeness-demanding** | rigid fit over fixed topology | requires `support == index` | else `Unresolvable` |

"Strict" is just the last row. Everything else flows over present support. This is
the gappy-`Coverage` resolution, reused on the entity axis.

### Two partiality sources, kept distinct

A masked model is only honest if it does **not** conflate:

- **absence** — a key was never measured here → lives in the *support / mask*;
- **op-failure** — a key is present but the op is undefined there (normalize a zero
  vector, slerp antipodes) → an ordinary per-element `Unresolvable`, **not** a
  support change.

This matches signals exactly: a signal's support is *data presence*; an antipodal
blend makes `at(t)` `Unresolvable` *in*-support without shrinking the support. So:
support = presence; reductions are **strict over op-failures** but **flow over
absences**. Keeping these apart is what makes the mask honest rather than mush.

### Where the mask comes from — construction is strict

Absence must be *deliberate*, never a silent catch of op-failure, or the two sources
blur back together. So **construction is strict**: `Bundle.of([resolvers])` and
`from_array` gather their inputs and are `Unresolvable` if any element is — matching
`Signal.from_samples`, which fails to *build* on a bad sample rather than dropping
it. A mask is set only **explicitly** (a presence argument / sentinel at
construction — an occluded frame's missing markers) or **produced** by an operation
(`where`, a `zip` intersection, `traverse` resampling into a gap). Op-failure stays
strict; absence stays data-driven.

### How lifting aligns the index — the axis kind decides

The one place a `Bundle`'s lift genuinely diverges from a `Signal`'s: a **metric**
axis **unions** indices (reconstruction fills between samples), but a **nominal**
axis **intersects** them (there is nothing to reconstruct a missing key from). So
`Signal`'s `decide_lifted` aligns on the *union* of sample instants (∩ supports),
whereas `Bundle`'s `zip` aligns on the *intersection* of keys. Both still
**intersect supports**. Same principle, opposite index-set operation — a direct
consequence of nominal-vs-metric.

---

## The grand analogy — and where retargeting lives

Generalize "the index" past `int`/`str`: the index is a **groundable domain**, the
entity-axis analog of `Frame` (space) and `Timeline` (time). The whole library then
snaps into one table:

| | **space** | **time** | **plurality** |
| --- | --- | --- | --- |
| identity domain | `Frame` | `Timeline` | **`Roster`** |
| correspondence map | `Transform` | `TimeMap` | **`RosterMap`** |
| a field over it | `Point3` (single) | `Signal[V]` | **`Bundle[V]`** |
| support | (n/a) | `Coverage` | key-set |
| recover the map from landmarks | point correspondence | `TimeMap.through` *(built)* | roster correspondence |

The punchline: a **`RosterMap`** — a partial correspondence between two rosters
(source-skeleton markers ↔ target-skeleton joints) — is the entity-axis mirror of
the `TimeMap.through` work already shipped. **That mapping is what motion
retargeting *is*.** The sibling `retarget` project is not an incidental consumer of
this layer; retargeting **is** roster-correspondence the way synchronization **is**
time-correspondence. We build the field (rung 2) now and *reserve* the
grounding/correspondence layer (rung 3) for when `retarget` reaches for it — exactly
as `TimeMap.through` shipped while its estimators stayed parked.

A `RosterMap` carries only the **identity** correspondence — *which* entity is which.
The **geometric** transfer of retargeting (where a target joint actually goes given
the source markers) is a fitted/numeric map layered on top — *not* part of
`RosterMap`, the same way `TimeMap.through` recovers the alignment but the estimator
that *discovers* the landmarks is parked numerics.

The **identity ladder**:

1. positional (`int`) — anonymous;
2. keyed (labels) — nominal identity; **← build this (rung 2)**;
3. groundable `Roster` + `RosterMap` correspondence — **built (rung 3, retarget's home)**.

A `Roster` is to the nominal axis what `Coverage` is to time: the **support set** for
that axis (a set of keys vs a set of intervals), with the same union / intersection /
difference algebra — rung 3 just adds identity and grounding on top. So even the
*support types* mirror across the table, not only the fields and maps.

---

## Collection over time = composition; the `Blend` is the hinge

`Signal[Bundle[V]]` works because the signal core never looks inside `V`. The two
supports **multiply** into the `(T, N)` **occlusion mask** that motion-capture data
actually is — `Coverage(time) × keyset(entity)` — undefined at `(t, k)` iff *t* is
in a temporal gap **or** *k* is absent at *t*. The correctness contract is the
**commuting square**:

```
field.at(t).at(k)  ==  field.at(k).at(t)
```

sample-then-index = index-then-sample, undefined under the same condition.
Composition gives this for free; a bespoke `(T, N, d)` type would force you to
re-prove it by hand. And the proposed representation *satisfies* it by construction:
`field.at(t)` masks key *k* unless *k* brackets *t* on both sides — which is exactly
the condition under which *k*'s own trajectory `field.at(k)` is defined at *t*. Both
sides reduce to the same per-key bracketing.

The result that shows the abstraction is carved at the joint: **the bundle's
`Blend` is partial, and that one fact lets a single `Signal[Bundle]` serve two data
regimes that look like they need different types.**

- **Fixed-roster mocap** — same keys each frame, persistent identity → per-marker
  trajectories exist; interpolating the cloud between frames blends each marker over
  the keys present at *both* bracketing samples (intersection → per-`(t,k)` gaps when
  a marker drops out). The `Blend` **succeeds**.
- **Anonymous, variable-`N` LIDAR** — each sweep is a *set* with no cross-frame
  identity and a different count; you genuinely *cannot* interpolate between sweeps.
  The bundle `Blend` over disjoint rosters returns `Unresolvable` → querying
  *between* samples is honestly undefined, while querying *at* a sample returns that
  exact sweep.

The bundle `Blend` is the **elementwise lift of the inner `V`'s `Blend`**, partial
on roster match — so it is correct by reuse, not by re-derivation. (This also means
a type's `Blend` is shared between its `Signal` facade and its `Bundle` facade: one
per-type "geometry kit" of array (un)stacking + `Blend`.)

### The two compositions, and `traverse`

`Signal[Bundle]` (one clock, frames — synchronized capture) and `Bundle[Signal]`
(per-entity independent clocks — heterogeneous/asynchronous sensors) are different
objects:

- **`traverse` / `sequence`:** `Bundle[Signal] → Signal[Bundle]` — resample each
  signal onto a caller-given common `Sampling` (explicit, mirroring `resample`), then
  stack. **Partial:** a signal undefined at a sample time → that cell is masked.
  *This is where the `(T, N)` mask is created*, from the per-signal `Coverage`s.
- its inverse, **distribute:** `Signal[Bundle] → Bundle[Signal]` — project out each
  key's trajectory. **Total.**

---

## Value representation

Resolve to **struct-of-arrays**, mirroring `SampledSeries`' `(T, d)`. Two encodings
behind one value interface:

- **dense + mask** — the full roster of `N` keys, an `(N, d)` array, a boolean
  presence `(N,)`. Carries the *roster vs support* distinction natively (declared
  keys vs present keys). Matches numpy and makes `Signal[Bundle]` a clean
  `(T, N, d)` + `(T, N)` mask. **Default.**
- **sparse** — only present keys + their `(M, d)` values; collapses roster and
  support unless an explicit roster is attached. The escape hatch for anonymous /
  variable-`N` clouds.

`Bundle.at(key) → Point3` bridges back into the static algebra, exactly as
`Signal.at(t)` does. Storage order is **canonical** (e.g. sorted keys) for
reproducible arrays/`repr`/equality, but the *semantics* are order-free: a bundle is
a map, not a sequence, and `zip` aligns **by key identity**, never by storage
position (the decisive reason keyed beats positional). The **frame is a bundle-level
attribute** — one shared coordinate frame for the whole cloud, like a signal's one
timeline; per-element frames are out of scope.

---

## Three layers of partiality

| Layer | Question | Carried by | Example failure |
| --- | --- | --- | --- |
| **resolver-level** | can I *build* the collection? | `decide()` → `Unresolvable` | mismatched key/value counts; duplicate keys |
| **presence-level** | is key *k* present? | the support / mask | `at(k)` for an occluded marker |
| **op-level** | present, but is the op defined here? | `Unresolvable` *in*-support | `normalized()` of a zero point; slerp antipodes |

(Signals' two layers — build + `Coverage` — plus the same op-level `Blend` failure
signals already have.)

---

## The algebra (the standard FP hierarchy)

- **Construction** — `Bundle.of([resolvers])` (gather + stack — the reification of
  the ad-hoc list-combinators that already exist, e.g. `Point3.centroid([…])`),
  `from_array((N,d) array[, keys])`, `from_map({key: resolver})`. Mirrors
  `Signal.from_samples`/`sampled`.
- **Functor** (`map`) — typed per-op lifts (`transformed_by`, `normalized`), **not**
  `map(callable)` (which would reopen the closed DAG).
- **Applicative** — broadcast a single primitive over the cloud; `pure` = a constant
  cloud over a roster.
- **Foldable** — `centroid() → Point3`, `count() → Scalar`, extremes; collapse the
  entity axis (empty support → `Unresolvable`). (`bounds()`/AABB deferred — wants a
  result type.)
- **Traversable** — the `Bundle[Signal] ↔ Signal[Bundle]` bridge above.
- index / filter — `at(key) → V` (bridges to the static algebra), `present(key) →
  Bool` (the decidable analog of `Signal.defined_at`), `keys()` / `support()`
  (concrete key collections, as `Sampling` exposes its times — upgraded to a `Roster`
  at rung 3), `where(keys)`.

---

## The primitive set

Mirrors the signal layer: a generic, `V`-agnostic core + thin per-type facades.

| Item | Mirrors | Role |
| --- | --- | --- |
| `Bundle[V]` (resolver base) | `Signal[V]` | a deferred field over a nominal axis |
| `BundleValue[V]` (resolved) | `SampledSeries[V]` | SoA: roster keys + values + presence |
| `Point3Bundle` / `Vec3Bundle` / `ScalarBundle` / `Direction3Bundle` / `TransformBundle` | `…Signal` facades | per-type facade; `Point3Bundle` *is* a point cloud |
| `Blend[V]` *(reused)* | — | already exists; the bundle `Blend` lifts it elementwise |
| `Roster` | `Timeline` / `Frame` | identity domain for entities — **built (rung 3)** |
| `RosterMap` | `TimeMap` / `Transform` | correspondence between rosters — **built (rung 3); the retarget seam** |

(Names provisional. `Bundle` carries the fiber-bundle resonance — a fiber `V` over
each base/index point — which is exactly the structure.)

### Layering

`bundle` sits parallel to `signal`, value-agnostic over any `V`, importing the
lower geometry/temporal layers but **not** `signal`. `signal` may host a `Bundle`
value (`Signal[Bundle[V]]`), so the edge is **`signal` *can* depend on `bundle`,
never the reverse** — the same discipline that keeps `timeline` below `signal`.

```
core < … < point3
          < signal              (+ timewarp)
          < roster < rostermap         # rung 3: entity-axis identity domain + correspondence
          < bundle                     # bundle imports geometry + roster/rostermap; signal may host a bundle V
```

---

## Roadmap (staged)

| Phase | Delivers |
| --- | --- |
| **1** | `Bundle[V]` core + `BundleValue[V]` + per-type facades; construction, `at`/`present`/`count`/`where`; first-class support — **DONE, all five facades** (`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3` `Bundle`): generic core + shared `decide_gathered`/`decide_where`/`decide_member_at`; `of`/`from_array`/`from_map` (+ wider `roster` for absent keys), `at`→ primitive, `where`, and a fold (`centroid`/`mean`; `Direction3.mean` partial; `Transform` none — SE(3) is numerics); strict construction |
| **2** | the algebra — `zip`-by-key (lift on the key *intersection*: `Scalar` `+ - * /`, `Vec3` `+ -`/`dot`, `Point3` `displacement_to`/`distance_to`), broadcast (`transformed_by`), folds (`sum`) — **DONE** (`decide_zipped` + `decide_mapped` helpers, mirroring signal lifting) |
| **3** | over-time: the bundle `Blend` (elementwise lift) so `Signal[Bundle[V]]` works; the `(T, N)` occlusion mask — **`Point3BundleSignal` DONE** (`from_frames` + per-frame mask, `at(t)`→`Point3Bundle`, inherited time-ops; occlusion falls out of the key-intersection blend) **+ `key(k)`→`Point3Signal` DONE** (the *distribute* column — one marker's trajectory; its support gaps at occlusions/temporal dropouts so the commuting square `at(t).at(k) == key(k).at(t)` holds **under the default reconstruction**; a present-frames projection can't mirror `hold`/`nearest`/`wrap`, so `key()` refuses those as Unresolvable). Remaining: a *fully general* `key()` (delegating reconstruction, all kernels/boundaries); other bundle-signal types; full `traverse` (`Bundle[Signal] → Signal[Bundle]`, the reassembly direction) |
| **4** | sparse encoding for anonymous / variable-`N` clouds |
| **R** | `Roster` + `RosterMap` (entity grounding + correspondence) — the retarget seam — **DONE (2026-06-25, pulled by retarget).** `Roster` = the entity-axis support set (the nominal-axis `Coverage`): `of`/`empty`, total `union`/`intersection`/`difference`, `count`→`Scalar`, `contains`→`Bool`, order-free set equality; a `Bundle.support` is now a `Roster`. `RosterMap` = the identity correspondence (the nominal-axis `TimeMap`): `of`(landmarks)/`identity`/`known`, `@`(total), `inverse`(partial: non-injective), `source`/`target`→`Roster`, `maps`→`Bool`; **applied to data via `Bundle.relabel`** (the identity transfer, across all five facades, partial on a target collision). The geometric transfer on top stays parked numerics — `RosterMap` carries identity only, exactly as designed |

Each phase follows the same definition of done as any primitive
([`CHECKLIST.md`](../CHECKLIST.md)): private resolver + documented facade,
`Unresolvable` (never raise) for value-dependent partiality, unit + partiality +
propagation tests, README/CHECKLIST rows, 100 % coverage, `ruff`/`mypy --strict`.

---

## Scope fences (deliberately out)

- **Multi-subject** (index = subject × marker) → a *product* of nominal axes; use
  nesting (`Bundle[Bundle[V]]`) for now; a flattened product axis is a later
  optimization.
- **Heterogeneous collections** (different types per slot) → **out**; that is a
  record/struct, not a homogeneous `Bundle[V]`.
- **Meshes** → a `Bundle[Point3]` *plus topology* (edges/faces); connectivity is a
  separate later layer, not part of the cloud substrate.
- **KD-trees / nearest-neighbor / ICP correspondence** → numerics; fungeom *calls*,
  does not *be* — the same fence as DTW. The `RosterMap` they produce is the
  decidable return type.
- **Interpolating anonymous, variable-`N` clouds** → genuinely undefined →
  `Unresolvable` by design, not a gap to fill.
- **Zipping anonymous clouds** → positional `zip` is correspondence-*by-position*,
  valid only when the caller guarantees the two clouds correspond slot-for-slot.
  Clouds with no shared identity are **not** zippable; producing a correspondence
  between them is a numeric matcher (parked) whose output is a `RosterMap`.

---

## Decisions log (settled here)

- **Plurality is an outer axis; a collection is a field over a *nominal* axis** — the
  same constructor as `Signal` (a field over the metric *time* axis). Over-time =
  `Signal[Bundle[V]]` by composition, **not** a bespoke `(T, N, d)` type.
- **Support is first-class and total** (defaults to full); strict-vs-masked is a
  property of *operations*, not of the type. Two partiality sources (absence vs
  op-failure) kept distinct.
- **Keyed, identity-aligned** (rung 2): `zip`/folds align by key, not position.
  Dense+mask is the default encoding; sparse is reserved for variable-`N`.
- **Mirror-and-converge, do not refactor `Signal`:** build `Bundle` in the signal
  mold; extract a shared `Field`/axis base *only* if a third axis ever demands it.
  Premature unification is the live risk.
- **Build rung 2, reserve rung 3:** `Roster`/`RosterMap` were written into the
  roadmap (the retarget seam is too central to omit) but not built until pulled —
  **now pulled and built (2026-06-25)**, as `retarget` reaches for the seam.
  `RosterMap` carries *identity only*; the geometric transfer stays parked numerics.
- **`where` on a collection-over-time narrows the *work*, by pushdown — not only the
  answer (2026-08-14).** The obvious reading of "restricting is not a rebuild" is to
  decide the source and drop keys from each sample, and that is still the fallback and
  still what defines the meaning. But it makes a selection of k of N markers cost N: the
  reported case built 1.7M `Point3`s (the whole 6,074-point cloud at all 281 frames) to
  fit a plane to 2,064 of them at *one* instant, and `where` saved 1%. So a source may
  implement `_narrowed_to(kept)` and return an equivalent signal that materializes only
  those keys — the array-backed carrier narrows by column, and `restrict` / `resample` /
  `reparameterize` push into their own source, because a time op never reads a key.
  Two rules keep it honest, and both are load-bearing:
  **(a)** a node **declines** (returns `None`) whenever a key it would drop could carry
  partiality of its own — a dropped key must never turn an `Unresolvable` into a value.
  That is why the point-cloud carrier narrows (a `(T, N, 3)` float array has no per-member
  partiality) and the *pose-set* carrier does not (a member `Transform` can be
  Unresolvable, and narrowing past it would silently repair the signal).
  **(b)** the pushdown is **skipped when the source is already decided**: narrowing beats
  deciding in full, but never beats reading a decision that has been made.
  This is an evaluation strategy, not a semantics — the two paths must agree sample for
  sample, `Unresolvable`s and reasons included, and `tests/cross_cutting/test_entity_narrowing.py`
  pins that by counting materialized points rather than by timing anything.
- **The per-point object layer is off the frame-stack path (2026-08-14).** A cloud carrier
  world-anchors its whole `(T, N, 3)` stack with **one** transform and materializes each
  frame through the bulk `as_point3_block` (one copy, one freeze, rows as views), instead
  of building a `Point3` resolver per point per frame and deciding it. The anchoring keeps
  the per-point coordinates *exactly*, which costs ~17 ms where the old path cost 27 s.
  (**Superseded 2026-08-20:** this originally read that summing the rotation's scaled
  columns was bit-identical to the per-point `rotation @ p + t` while `block @ rotation.T`
  was not. That was true only on the machine it was written on — the per-point side still
  went through BLAS, so the two agreed only where gemv associated the same way, and the
  test asserting it failed on x86-64 from the day it was written. Both sides now share one
  `dot3` expression; see the summation-order entry below.) Note this is **not** the
  struct-of-arrays `BundleValue` this document's *Value representation* section still
  describes as the target; `members` remains a dict of `Point3Value`, and that dict is now
  the floor on the cost. Closing the rest of the gap to numpy means changing the *value*,
  which is a real design change and not one made under a performance report.
- **A cloud measured against a carrier answers a whole frame at once — and the fold was
  never the cost (2026-08-20).** `FaceSignal.clearance` / `PlaneSignal.signed_distance`
  over a cloud built one resolver per member per instant, so a *fold* of that field
  (`clearance(cloud).min()`) cost ~57× reading back the whole unreduced field — asking for
  less data cost far more. The reduction was **0.5%** of that: the fold merely forces
  `decide()`, and it was `decide()` that walked the static algebra `T·N` times while a
  batched kernel sat beside it in `resolve_over`. So the fix is `decide_lifted_block` —
  `decide_lifted`'s alignment (shared now, via `align_signals`, so the two cannot drift on
  *which instants* they answer) with the member axis answered in arrays through
  `FaceValue.clearance_block` / the `_block` twins on `Region2Value` / `PlaneValue`.
  Fixing it here rather than in the fold's readback is what makes `at(t)`, `key(k)` and
  every other `decide()` consumer fast too. `min().resolve_over`: 15.3 s → 0.16 s at 1,000 points,
  **40.8 s → 0.74 s at 6,074** (1.7M point-instants); `at(t)`: 7.0 s → 0.15 s.
- **The batched twins are spelled for bit-identity, not for speed alone (2026-08-20).**
  Each `_block` method reproduces its scalar sibling's exact arithmetic — the same cross
  products and `hypot` edge lengths in the even-odd test, `argmin`'s first-minimum matching
  the scalar loop's strict `<`, length-3 matrix-vector products that associate as the scalar
  `np.dot` does. Verified against `002e9e7`: every decided value, all five folds, `at(t)`
  and off-knot reconstruction are `array_equal`, on a **non-convex** footprint under a
  moving pose (an identity pose hides reassociation; a convex one hides the clamp).
- **A signal can be asked for its *index* without materializing its values (2026-08-20).** The
  batched lift needs three things from the cloud it measures — when it is sampled, where it is
  defined, which keys it declares — and was getting them by deciding it in full, building 1.7M
  `Point3Value` objects it never read (two-thirds of the remaining cost; the coordinates come from
  `_decided_grid` in 64 ms). `_sample_index` is the pushdown for exactly those three, answered by a
  dense carrier from its own `sampling`. The alignment rule moved down with it, to
  `aligned_instants`, stated against time bases instead of decided series — that is what lets a lift
  obey the rule without materializing an operand, while keeping one definition shared with the
  per-instant `decide_lifted`. **An index is deliberately not a proof of resolvability**: a dense
  carrier answers it without checking whether its frame is grounded, and that partiality surfaces
  from the grid readback instead, with the identical reason. Same shape as `_narrowed_to` above —
  *a node that knows the shape of its answer can report it without computing it.*
- **Only now is `BundleValue` the floor (2026-08-20).** After the index pushdown, what remains is
  ~275 ms building the per-frame dicts and ~240 ms walking `support()` over 1.7M keys, against
  ~250 ms of actual geometry. The earlier claim in this log that the dict was *already* the floor
  was wrong — asserted from the shape of the numbers rather than a profile, which put two-thirds of
  it somewhere else entirely. It is the floor now. It is still not a change to make under a
  performance report.
- **The summation order is fungeom's, not BLAS's (2026-08-20).** A small fixed-size product has
  three routes into BLAS — `np.dot` on two 3-vectors, `matrix @ vector`, `block @ matrix.T` — and
  BLAS may associate each differently per kernel and per architecture, so the three can return
  three different last bits for the same quantity. *Which* of them agree is platform-dependent:
  they coincide on arm64 macOS and diverge on x86-64 Linux. Every bit-exactness claim in this log
  was therefore only ever verified on one architecture, and the `002e9e7` anchoring test failed on
  Linux from the day it was written — invisible because that branch was never pushed and CI is
  x86-64 only. `dot2` / `dot3` / `norm3` in `core.arrays` now fix the order: one written expression,
  broadcasting over any leading axes, called by the per-item path and its batched twin alike. They
  cannot disagree — not because a machine was found on which they were equal, but because they
  evaluate the same operations in the same order. **The general rule this leaves behind:** a scalar
  method and its `_block` twin must *share* the expression, never merely be tested equal on the
  machine at hand; "we compared them and they matched" is a statement about a laptop, not about the
  library. Cost: values move up to ~1 ulp on platforms where BLAS was reassociating (none on
  arm64). Taken deliberately — a graph should resolve to a value, not to a value that depends on
  where it was resolved.
- **A pushdown has to reach the readbacks, not just `decide` (2026-08-20).** `where`'s entity-axis
  pushdown had been in `decide_where_over_time` since the first perf pass, and a narrowed cloud
  still paid for the whole cloud — because the batched lift never calls `decide` on it. It asks for
  the cloud's *index* and its *dense grid*, and both fell through to the generic path. The lesson
  generalizes past this one node: **once a fast path exists beside a slow one, every new entry point
  has to be taught about it, and the ones that forget are invisible** — the answers stay right, only
  the cost is wrong. `where` narrowing to 38% of a cloud bought 3% for two releases before anyone
  measured it. Now: 0.876 s → 0.323 s, and 1.05× the equivalent dense cloud rather than 2.63×.
- **`resolve_over` was unified onto that same kernel, and this moved values (2026-08-20).**
  It previously inverse-transported the query into the static patch's frame and split the
  distance via a GEOS lateral term — mathematically equal to the per-instant path but a
  *different algorithm*, disagreeing with `at(t)` by ~7e-15 relative under a moving pose
  while its docstring claimed a match. Both now run `_face_clearance_block`, so the readback
  and the decided field are the same computation; the cost is that `resolve_over` alone
  shifted ≤1.8e-15 from `002e9e7`. Chosen deliberately: one algorithm that agrees with
  itself beats two that agree to within a rounding error.
- **What a fold means was *not* changed, and the tempting rewrite would have (2026-08-20).**
  The reported fix was "resolve the fold over the sampling through the bundle's batched
  readback and reduce in arrays". That is min-of-lerp; `min()` has always meant lerp-of-min
  — fold at the source's own knots, then reconstruct (`decide_folded`). On two members that
  cross, `sig.min().at(0.5)` is `0.0` and the rewrite gives `5.0`. It reads as equivalent
  only when the target grid *is* the source's knots, which is what the report measured.
  `tests/cross_cutting/test_batched_lifts.py` pins the distinction so it cannot be
  "optimized" away later.

**Status:** spine + **phases 1–3 complete, and rung 3 (phase R) built.** Phases 1–2: all five bundle facades
(`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3`) — generic `Bundle[V]` core +
`BundleValue[V]` + shared decide helpers, first-class maskable support, strict
construction, `of`/`from_array`/`from_map`, `at`/`present`/`count`/`where`, per-type
folds, and the key-aligned algebra (`zip` on the key intersection, `broadcast` map,
`sum`). **Phase 3: `Point3BundleSignal` = `Signal[Bundle[Point3]]`** — collection
over time *by composition* (the V-agnostic signal core hosts a `BundleValue` via the
bundle `Blend`), with `from_frames` + a per-frame occlusion mask, `at(t)`→`Point3Bundle`,
and the inherited time-ops; the `(T,N)` occlusion mask falls out of `Coverage` ×
per-frame entity mask. **`key(k)`→`Point3Signal`** projects one marker's trajectory (the
*distribute* column), its support gapping at occlusions/temporal dropouts so the commuting
square `at(t).at(k) == key(k).at(t)` holds *under the default reconstruction* (linear +
`undefined`); it refuses `hold`/`nearest`/`wrap` (which a present-frames projection cannot
mirror) as Unresolvable rather than disagree. **Rung 3 (phase R, 2026-06-25):** `Roster` (the
entity-axis support set — the nominal-axis `Coverage`: `of`/`empty`, total set algebra, `count`,
`contains`, order-free equality) and `RosterMap` (the identity correspondence — the nominal-axis
`TimeMap`: `of`/`identity`/`known`, `@`, partial `inverse`, `source`/`target`, `maps`), wired into
the bundle as `Bundle.support`→`Roster` and `Bundle.relabel(RosterMap)`→bundle (the retarget
identity transfer, across all five facades). **`TransformBundleSignal` added (2026-06-25)** — the
pose-set-over-time companion to `Point3BundleSignal` (`Signal[Bundle[Transform]]`, a skeleton's
joints over time); its SE(3) bundle blend is the elementwise slerp lift, **strict over op-failure**
(an antipodal joint makes the whole interpolated pose-set Unresolvable, never disguised as absence) —
which is why it has no `key()` (the entity-axis commuting square needs a *total* blend, which only
the `Point3` lerp provides). Remaining: a fully-general `key()` (delegating reconstruction), the
remaining bundle-signal types (`Scalar`/`Vec3`/`Direction3`), full `traverse` (`Bundle[Signal] →
Signal[Bundle]`), and sparse encoding (phase 4). Each phase to the gate.
