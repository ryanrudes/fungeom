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
3. groundable `Roster` + `RosterMap` correspondence — **reserved (rung 3, retarget's home)**.

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
| `Roster` | `Timeline` / `Frame` | identity domain for entities — **reserved (rung 3)** |
| `RosterMap` | `TimeMap` / `Transform` | correspondence between rosters — **reserved (rung 3); retarget** |

(Names provisional. `Bundle` carries the fiber-bundle resonance — a fiber `V` over
each base/index point — which is exactly the structure.)

### Layering

`bundle` sits parallel to `signal`, value-agnostic over any `V`, importing the
lower geometry/temporal layers but **not** `signal`. `signal` may host a `Bundle`
value (`Signal[Bundle[V]]`), so the edge is **`signal` *can* depend on `bundle`,
never the reverse** — the same discipline that keeps `timeline` below `signal`.

```
core < … < point3
          < signal   (+ timewarp)
          < bundle                       # bundle imports geometry; signal may host a bundle V
```

---

## Roadmap (staged)

| Phase | Delivers |
| --- | --- |
| **1** | `Bundle[V]` core + `BundleValue[V]` (dense+mask) + per-type facades; construction, `at`/`keys`/`support`/`where`; first-class support |
| **2** | the algebra — functor lifts, `zip`-by-key, folds (`centroid`/`count`); broadcast |
| **3** | over-time: the bundle `Blend` (elementwise lift) so `Signal[Bundle[V]]` works; `traverse`/`distribute`; the `(T, N)` occlusion mask |
| **4** | sparse encoding for anonymous / variable-`N` clouds |
| **R** | **reserved:** `Roster` + `RosterMap` (entity grounding + correspondence) — the retarget seam; build when pulled, not speculatively |

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
- **Build rung 2, reserve rung 3:** `Roster`/`RosterMap` are written into the
  roadmap (the retarget seam is too central to omit) but not built until pulled.

**Status:** design only — nothing built yet. This note is the spine; implementation
follows the staged roadmap above, one phase at a time, each to the gate.
