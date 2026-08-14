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
  of building a `Point3` resolver per point per frame and deciding it. The anchoring is
  written as a sum of the rotation's scaled columns rather than `block @ rotation.T`
  *deliberately*: only that spelling is bit-identical to the per-point `rotation @ p + t`
  it replaced (BLAS reassociates, which moved coordinates ~4e-13 relative), and the
  fidelity costs ~17 ms where the old path cost 27 s. Note this is **not** the
  struct-of-arrays `BundleValue` this document's *Value representation* section still
  describes as the target; `members` remains a dict of `Point3Value`, and that dict is now
  the floor on the cost. Closing the rest of the gap to numpy means changing the *value*,
  which is a real design change and not one made under a performance report.

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
