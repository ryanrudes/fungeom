# Time in fungeom

A design note for adding **time** to the library. It is the canonical, settled
plan, synthesized over four design passes — written so a future contributor (or
agent) can build the rest from it. Read [`README.md`](../README.md) first for the
decidability core; this note assumes those concepts (`decide()`,
`Resolvable`/`Unresolvable`, facade-over-concrete-resolvers, `<Primitive>.Value`)
and reuses them wholesale.

---

## The spine: fungeom is a decidability engine, geometry is just instance #1

The thing fungeom actually *is* is not "geometry". It is a **decidability engine
over a closed, lazy, immutable DAG**, in which partiality is reified:
`decide() -> Resolvable | Unresolvable`. Geometry was the first thing modeled in
it. **Time is the natural second.** It has the same shape — an oriented affine
space, framed relativity (clocks), value-dependent partiality (off-coverage,
unsynced) — and it slots into the same machinery with no new core concepts.

And the two **compose**: a `Signal[Point3]` is a point that moves. The payoff of
building time *in the same engine* is that geometry-over-time falls out of the
existing combinator algebra rather than being a parallel stack.

---

## Time is an oriented 1-D affine space — plus order

Time mirrors space almost exactly, one dimension down. The mirror is literal: the
time primitives are built the same way as their spatial counterparts and inherit
their partiality patterns.

| Time | Mirrors | Algebra |
| --- | --- | --- |
| `Instant` | `Point3` | an affine **point** on the timeline |
| `Duration` | `Vec3` | the **difference vector space** of the line |

The affine algebra is the usual one, restricted to 1-D:

```
Instant  - Instant   = Duration        # displacement between two moments
Instant  + Duration  = Instant         # shift a moment
Duration + Duration  = Duration        # combine spans
Instant  + Instant   = undefined       # no algebraic sum of two moments
```

Affine combinations generalize this: `Σ wᵢ · instantᵢ` is

- a **moment** (an `Instant`) iff `Σ wᵢ = 1` (e.g. a midpoint, a weighted mean),
- a **duration** (a `Duration`) iff `Σ wᵢ = 0` (a difference, a derivative stencil),
- otherwise **`Unresolvable`** — exactly as `Point3.affine` already is for space.

### The one way time exceeds space: a total order

A 1-D affine space is *almost* all of time. The one genuinely extra structure is
that the line is **totally ordered** — there is a before and an after. Space has
no such thing. That single addition is the source of every time-side primitive
with no spatial analog:

- **`Interval`** — an ordered pair of instants `[a, b]` with `a ≤ b`.
- **`Coverage`** — a set of disjoint, sorted intervals (where data *exists*).
- **monotonic warps** (`TimeWarp`) — order-preserving reparametrizations.

If you ever wonder "why does the time side have a thing space doesn't?", the
answer is always: *order*.

---

## A clock is a frame; alignment is grounding

`Timeline` mirrors `Frame` exactly. A local clock is **grounded** to a chosen
**master** clock through a chain of affine maps, just as a coordinate frame is
grounded to the world frame through a chain of transforms.

| Time | Mirrors | Meaning |
| --- | --- | --- |
| `Timeline` | `Frame` | a clock; grounded to master, or detached |
| `TimeMap` | `Transform` | the affine map between two clocks (offset + rate) |
| master timeline | `Frame.world` | the root clock; the chosen chart |

This makes synchronization a first-class, *decidable* problem instead of a
preprocessing hack:

- **Un-synced data is literally a detached timeline.** A recording whose clock
  has not been related to the master sits on a `Timeline.detached("camera_2")`.
  An `Instant` on it is **`Unresolvable`** in master time — the same way a
  `Point3` in a detached frame cannot be world-anchored. The reason names the
  ungrounded clock.
- **Aligning two recordings *is* computing the missing edge** — the `TimeMap`
  that grounds the detached clock to master. The alignment estimate (cross-
  correlation of an event train, a hand-clap landmark, a known trigger) *is* that
  edge. Once attached, every instant on that clock resolves.

### Two kinds of time map, kept separate on purpose

There are two distinct operations people lump together as "time warping", and
conflating them both creates a dependency cycle *and* is semantically wrong:

| | What it is | Type | Constraint |
| --- | --- | --- | --- |
| **Clock grounding** | relate one clock to another | `TimeMap` (mirrors `Transform`) | **affine** (offset + constant rate) |
| **Content warping** | reparametrize a signal's own time | `TimeWarp` | general **monotonic** |

Clock-grounding is affine because a physical clock differs from master by an
offset and a (near-constant) rate; that is all a `Timeline` chain ever needs, and
it keeps `Timeline`/`TimeMap` below `Signal`. Content-warping (dynamic time
warping a gait cycle, easing an animation parameter) is general monotonic and
lives *up* at the signal layer, where it can. Keeping them separate is what lets
`timeline` never import `signal`.

---

## A signal is a value with a time-shaped hole (the load-bearing idea)

This is the keystone. **`Signal[T]` is a `Resolver` whose *value* is a partial
function of time.** Its resolved value is not a `T` — it is a *function*
`time -> T`, carried as a domain plus an evaluator (or a sampling plus values).

```python
moving = Signal.from_samples(times, positions)   # a Signal[Vec3]
moving.at(Instant.seconds(2.5))                   # -> a Vec3 resolver (the hole filled)
```

`signal.at(instant)` **fills the hole and bridges back to the static graph**: it
yields an ordinary `Vec3` (or `Point3`, `Scalar`, …) resolver. From there the
*entire existing combinator algebra works downstream of a sample for free* —
`moving.at(t).norm()`, `a.at(t).distance_to(b.at(t))`, all of it. Time is the
only new thing; everything geometry already does composes after a sample.

### Two layers of partiality

A signal has partiality at *two* levels, and they are different questions:

| Layer | Question | Carried by | Example failure |
| --- | --- | --- | --- |
| **resolver-level** | can I *build* the function at all? | `decide()` → `Unresolvable` | corrupt / non-monotonic timestamps |
| **function-level** | is the function *defined at this time*? | `Coverage` | sampling at `t` in a dropout gap |

`Signal.decide()` answers the first. `signal.at(t).decide()` answers the second:
asking for a value inside a coverage gap is `Unresolvable`, with a reason that
names the gap. Both ride the existing `Resolvable`/`Unresolvable` channel.

### The reconstruction contract (what a `Blend` and a kernel may assume)

Reading a signal at `t` composes a `Coverage` support, an `Interpolation` kernel, a
`Boundary`, and a `Blend`. Three invariants tie them together. They stayed *implicit*
until a **support-changing** blend — one whose output is narrower than its inputs
(e.g. a point-cloud blend that keeps only the markers present in *both* frames) —
stress-tested them into the open, so they are worth stating: every prior blend was
support-*preserving*, and the assumptions only held by accident.

1. **Support governs *where*; the value carries *what*.** `t` must lie in the support
   (off it, the boundary clamps past the outer hull, else `Unresolvable`). *Within*
   support the reconstructed value may still be partial or narrower: a **value-partial**
   blend (slerp of antipodes) is `Unresolvable` at `t` though `t` is in support; a
   **support-changing** blend yields a *value* whose own support is narrower than the
   signal's. A signal's support is about *temporal* presence, not the value's internal
   completeness.

2. **An exact sample is the sample — never routed through the blend.** For every
   kernel, evaluating at `t == times[i]` returns `values[i]` verbatim; the blend is
   invoked only *strictly between* samples. This *must* hold because a blend may be
   value-partial (slerp would wrongly fail at an exact sample adjacent to an antipode)
   or support-changing (a cloud blend would wrongly drop a key at an exact frame). A
   blend is otherwise a pure function and may be partial *or* support-changing.

3. **Boundary and support are per-signal.** A `hold`/`wrap` boundary clamps against
   *that signal's own* `[first, last]`. So a signal **re-reconstructed** from a subset
   of another's samples (the entity-axis `key()` slice of a cloud signal, say) matches
   the source's reconstruction only when that reconstruction is expressible as a single
   series over the subset — true for linear + `undefined`, false for select-style
   kernels (`hold`/`nearest`) and off-hull boundaries (`hold`/`wrap`). A derived signal
   that cannot match must **refuse** (`Unresolvable`), not silently disagree —
   decidability applied to reconstruction itself.

### Why *not* the free-variable / open-graph alternative

A tempting design is to make `Instant` a **free variable**: a special leaf so
that *any* resolver mentioning it automatically becomes a function of time, and
"sampling" is substitution. **We reject this.** It corrupts the core:

- it **opens the closed DAG** — leaves are no longer all literals/known values;
- it **breaks memoized `decide()`** — a node's decision now depends on an ambient
  binding, so the identity-keyed cache is no longer sound;
- it **bifurcates `Unresolvable`** — "unresolvable here" vs "unresolvable
  everywhere" become tangled, and the single reason-carrying failure type splits.

The **function-as-value** model avoids all of this. Every `Instant` in the graph
stays a *literal, known value*; the function-ness lives *inside* a `Signal`'s
value, behind one ordinary resolver. The DAG stays closed, `decide()` stays
memoized, `Unresolvable` stays single. (The ergonomic win the free-variable model
promised — lifting the whole static algebra over time — we recover deliberately
and safely via pointwise lifting; see below.)

---

## Real data is discrete, irregular, gappy, and unsynced — so reify the time axis

A naive "signal = array of samples" conflates three independent things. Real
motion-capture data (the driving use case — see the sibling **retarget** project)
forces them apart:

| Concern | Primitive | What it captures |
| --- | --- | --- |
| **when** samples were taken | `Sampling` | strictly-increasing real timestamps — **jitter and all** |
| **how to read between samples** | `Interpolation` + `Boundary` | reconstruction of a continuous function |
| **where data actually exists** | `Coverage` | the supported region — **with holes for dropouts** |

Reifying `Sampling` (rather than assuming a fixed rate) is what makes the rest
honest: true per-sample `dt`, correct handling of jitter, and gaps that are
*data*, not a special NaN convention.

### Two faces of temporal data

Mirroring retarget's two track types, temporal data comes in two shapes that
**interconvert**:

| Face | Primitive | Examples |
| --- | --- | --- |
| continuous-ish samples | `Signal[T]` | marker position, joint angle, force |
| discrete occurrences | `EventSequence` | foot-strikes, claps, contacts, triggers |

The round trip is a worked path through the whole time stack:

```python
contact = (
    force.threshold(Scalar.of(5.0))   # Signal[Scalar] -> boolean Signal
         .edges()                     # rising/falling -> EventSequence
)
stance  = contact.intervals()         # EventSequence -> Coverage
foot_in_stance = foot_pos.restrict(stance)   # Signal restricted to where it matters
```

---

## Resampling = filter ∘ reconstruct ∘ sample

Changing a signal's time grid is **three orthogonal axes**, composed in order:

1. **reconstruct** — a property of the *source* (its `Interpolation` + `Boundary`),
2. **filter** — when *downsampling*, an anti-alias **pre-filter** applied first,
3. **sample** — onto the *target* `Sampling`.

```
resample = sample(target) ∘ reconstruct(source) ,  preceded by  pre-filter (if decimating)
```

- The **pre-filter** is mandatory for honest downsampling: `median` (essential
  for mocap **despiking** — markers flick to garbage), `gaussian`, `lowpass`.
- `derivative` / `integral` live here too, and they **pay off from real
  timestamps**: using each sample's true `dt` yields correct velocity from
  *jittery* data, where a fixed-rate assumption would not.

### Reconstruction is manifold-aware — handled by a `Blend` typeclass, not N cores

Reconstruction depends on what the samples *are*: you `slerp` rotations, you can't
average them componentwise.

| Sample type | Reconstruction (`Blend`) |
| --- | --- |
| `Scalar`, `Vec2`, `Vec3` | linear (componentwise) |
| `Direction3`, `Transform` | **slerp** (manifold geodesic) |
| `Point3` | world-space lerp (grounds the framed samples first) |

The *initial* plan was one facade per primitive (mirroring geometry). A spike
showed a better factoring: **one generic core** (`signals/series.py`: a
`Signal[V]` / `SampledSeries[V]` generic over the sample type) plus a small
**`Blend[V]` typeclass** — the single capability that differs by type
(`between(a, b, frac) → Resolvability[V]`). The `Interpolation` kernels
(`linear`/`hold`/`nearest`) are value-agnostic: they pick samples + a fraction and
defer the combination to the `Blend`. Each value type is then a *thin* facade
(supply a `Blend`, narrow `at` to the rich primitive). The decisive property: a
manifold or framed value type plugs in **without touching the core**, and a
capability gap (no geodesic between antipodes; an ungrounded frame) surfaces as an
ordinary **`Unresolvable`** — exactly what Python's type system *can't* express as
a constraint, the decidability core expresses as partiality. Five signal types
(`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3`) ride this one core today.

Real pipelines are therefore **compositions of `Signal -> Signal` combinators
ending in a sample** — never ad-hoc array surgery.

---

## Pointwise lifting

One `map` / `zip` mechanism **lifts fungeom's entire static algebra over time.**
`zip` aligns two signals onto a common `Sampling` (resampling as needed), then
applies a static combinator pointwise; `map` lifts a unary one.

```python
height   = foot_pos.map(lambda p: p.z())          # Signal[Vec3] -> Signal[Scalar]
torque   = arm_a.zip(arm_b, lambda a, b: a.cross(b))   # Signal[Vec3] x Signal[Vec3] -> Signal[Vec3]
```

This **recovers the elegance the free-variable model promised** — the whole
geometry algebra, lifted over time — but *inside* the closed-graph guarantees,
because each pointwise application is just `at(t)` plus a static combinator. It is
**not a "later" nicety**: real pipelines need `foot_pos.z()`,
`signalA.cross(signalB)`, etc. from the start.

---

## The user-facing layer: three tiers, all desugaring to the core

**Governing principle: every ergonomic affordance *desugars* to the rigorous
backend.** There is one source of truth — the decidable core — and the friendly
surface is a *view* of it, so it can never silently disagree with what `decide()`
says. This is the move the library already makes when a bare `2.0` coerces to a
`LiteralScalar`.

The surface is **three tiers of progressive disclosure** over the *same graph*:

| Tier | Audience | What you touch |
| --- | --- | --- |
| **0 — friendly** | "load data, clean it, ask a question" | numbers/arrays/tuples, `Signal.from_samples`, fluent verbs taking *physical quantities* (`Duration.ms(20)`), defaults for everything — never the word "decidability" |
| **1 — explicit** | "I care how it's reconstructed/aligned" | name `Interpolation`/`Boundary`/`Timeline`, `match` on decisions, inspect `Coverage`, choose alignment methods |
| **2 — theoretic** | "I'm extending the library" | `decide()`, the affine algebra, the generic-parameter axis, hand-written resolvers |

### Flagship tier-0 example

```python
raw   = Signal.from_samples(times, marker_xyz)     # jittery mocap, with gaps
clean = (
    raw.despike(window=5)                # median pre-filter, sample-count window
       .smooth(Duration.ms(20))          # a TIME window — 20 ms, not "20 samples"
       .resample(at_hz=120)              # onto a regular 120 Hz grid
)

clean.at(2.5)            # -> a Vec3   (a number coerces to an Instant by position)
clean[:].z()             # -> a Signal[Scalar]  (lift the whole channel)
height = clean[:].z()
stance = height.below(0.05).intervals()  # -> a Coverage (where the foot is down)
```

Note `smooth(Duration.ms(20))` takes a **physical duration**, not a sample count
— the window means the same thing regardless of rate, and `despike(window=5)`
takes a sample count where that is the natural unit. The user never types
"decidability", yet every line above is a node in the decidable graph.

### A tier-0 failure still teaches

When something is `Unresolvable`, the message is written for a human, naming the
geometry of the gap:

```python
clean.at(7.3)            # 7.3 s falls in a dropout
# Unresolvable: Signal[Vec3] has no value at t = 7.300 s — it lies in a gap
#   (6.812 s … 7.901 s, 1.089 s wide). Nearest sample: 6.812 s (0.488 s away).
#   To read through gaps, reconstruct with Boundary.hold (or .nearest / .clamp).
```

### Concrete ergonomic specifics

- **Coercion by position** resolves the `Instant` / `Duration` / `Scalar`
  ambiguity of a bare number: in `signal.at(2.5)` the `2.5` is an `Instant`; in
  `instant + 2.5` it is a `Duration`; in `signal.scale(2.5)` it is a `Scalar`.
- **Unit-bearing constructors** make the quantity unambiguous and readable:
  `Duration.seconds(...)`, `Duration.ms(...)`, `Duration.minutes(...)`,
  `Duration.hz(...)` (a period from a rate).
- **Pythonic operators and indexing** (all desugaring to named methods):

  | Sugar | Desugars to | Result |
  | --- | --- | --- |
  | `instant + duration` | `instant.shift(duration)` | `Instant` |
  | `instant in interval` | `interval.contains(instant)` | `bool`-ish decision |
  | `interval & other` / `\|` / `-` | total set ops | **`Coverage`** |
  | `signal[instant]` | `signal.at(instant)` | `T` |
  | `signal[t0:t1]` | `signal.restrict(...)` | `Signal[T]` |
  | `signal[t0:t1:Duration.ms(10)]` | `signal.resample(...)` | `Signal[T]` |

  Set ops on intervals return a **`Coverage`** because the result of subtracting
  or unioning intervals is generally several disjoint spans — so the *total*
  (always-defined) friendly ops live on `Coverage`. The **partial**,
  `Interval`-returning operations (`meet`, `join` — which can be empty / non-
  contiguous) are **named methods**, not operators, so the friendly operator never
  surprises you with an `Unresolvable`.
- **Immutable editing verbs** — `replace_at`, `without`, `concat` — each with a
  **decidable overlap check** (overlapping or out-of-order edits are
  `Unresolvable`, not silent corruption).
- **Informative `repr`** — `Signal[Vec3] over 0.0–12.4 s · 1500 samples @ ~120 Hz · 2 gaps`.
- **A temporal `resolver_tree`** — `viz` gains a coverage / gap / out-of-coverage
  ASCII view, the same way it annotates spatial unresolvability today.
- **numpy bridge** — `Signal.from_arrays` / `signal.to_arrays` for the array
  boundary, alongside the higher-level `from_samples`.

---

## Backend iron-outs

- **Tolerance is contextual, and only for values.** Numerical tolerance for
  *value* comparisons is derived from context — **half the local sample interval**
  — so "the same instant" means "within the grid's resolution". **Structural
  decidability stays exact**: monotonicity of a `Sampling`, ordering of an
  `Interval`, `Σw = 1` for an affine moment — all exact, never tolerant. A
  decision made *near a boundary* reports its **margin** so the caller can see how
  close it was.
- **`Signal.Value` is a value-level union.** It is
  `SampledFunction | ClosedFunction` — both exposing `evaluate(t)` **and**
  `coverage` — so there is **one uniform `Signal` resolver**, not two. The two
  variants are an implementation detail of the value, not a fork in the type.
- **Binary-op / lifting alignment semantics.** For `zip` / lifted binary ops:
  evaluate **both** operands on the **union of sample times within the
  intersection of coverages**; the **result coverage = the intersection**; the
  result is **`Unresolvable` iff that intersection is empty**.
- **Affine-origin coherence.** The master `Timeline` is the chosen **chart**: its
  `t = 0` is the representation origin. But the `Instant` *type* still forbids
  `instant + instant` — `Instant.epoch` is a **landmark**, not an algebraic zero.
  (Same distinction as a frame's origin point versus the zero vector.)
- **Filtering phase.** Filters are **zero-phase by default** (offline, batch — we
  can run forward+backward), with a **causal** option for when phase must be
  preserved.

---

## The super-generalizing core: time is instance one of a generic 1-D axis

Everything above — an **oriented 1-D affine parameter**, plus `Sampling`,
`Interpolation`, `Coverage`, and `Signal`-over-it — is generic over **any** 1-D
parameter. `Signal[T]` is really `Parameter -> T`; **time is the first, canonical
instantiation**. Other instantiations are real:

| Parameter | A signal over it is… |
| --- | --- |
| **arc length** | a curve resampled by distance |
| **0–1 animation parameter** | a normalized keyframe track |
| **phase** | a gait/cycle-locked signal |
| **frequency** | a spectrum (read-only; we do not build spectral *primitives*) |

**We name this generalization to keep the design honest and future-proof — but we
build time concretely.** Do **not** pre-extract a generic `Axis` / `Parameter`
abstraction now. That respects the library's deliberate non-genericity (one
concrete facade per primitive) and the standing preference against pre-building
speculative abstraction. The *factoring* should be visible — the affine-1-D /
sampling / interpolation / coverage seams kept clean — so that a later
arc-length or phase instance is a **refactor, not a rewrite**.

---

## Scope boundaries (out by design)

| Out of scope | Why / what to use instead |
| --- | --- |
| calendar / timezone / leap-second time | master clock is a monotonic real-seconds axis; use stdlib `datetime` for wall-clock |
| streaming / online / unbounded | the library is **batch over known data** |
| frequency-domain / spectral primitives | filters use the freq domain internally; no first-class FFT primitive |
| uncertainty on time or value | a future `Signal[Distribution]`, not now |
| multi-channel "take" containers | N markers = a **dict of co-sampled `Signal`s sharing one `Sampling`** — a plain container *above* the primitives, since the correctness-critical shared `Sampling` / common `Coverage` is already expressible |

---

## The primitive set

Each primitive is one facade class over private concrete resolvers, exactly like
the geometry primitives, with `<Primitive>.Value` for its value type. The
strategy objects (`Interpolation`, `Boundary`, `Align`) are **enum-free objects**
— small value classes, not string keys.

| Primitive | Mirrors | Role | Key `Unresolvable` case |
| --- | --- | --- | --- |
| `Duration` | `Vec3` | a span (difference vector of the line) | (mostly total; rate `Duration.hz(0)`) |
| `Instant` | `Point3` | a moment (affine point) | on a detached `Timeline`; `Σw ≠ 1`-style affine combos |
| `Interval` | — | an ordered `[a, b]` | `a > b`; empty `meet` |
| `Coverage` | — | sorted disjoint intervals | (total under `& \| -`; empty is valid) |
| `Timeline` | `Frame` | a clock grounded to master | detached (ungrounded) clock |
| `TimeMap` | `Transform` | affine clock-to-clock map | degenerate (zero/negative rate) |
| `Sampling` | — | strictly-increasing timestamps | non-monotonic / duplicate timestamps |
| `EventSequence` | — | discrete ordered occurrences | out-of-order events |
| `Signal[T]` | *(new shape)* | a value that is a partial function of time | corrupt build; off-coverage at `.at(t)` |
| `TimeWarp` | — | general **monotonic** reparametrization | non-monotonic warp |

Strategy objects: `Interpolation` (`linear`, `cubic`, `slerp`, …), `Boundary`
(`hold`, `nearest`, `clamp`, `error`), `Align` (`xcorr`, `landmark`, `trigger`).

### Layering DAG

The new primitives extend the existing acyclic layering. The critical edge:
**`signal` imports `timeline`; `timeline` never imports `signal`** (that is the
whole point of splitting affine `TimeMap` from monotonic `TimeWarp`).

```
core
  < scalar
      < duration
          < instant
              < interval < coverage
              < sampling
              < eventsequence
              < timemap < timeline
  < vec2 / vec3 < direction3 < transform < frame < point3
  < signal (+ timewarp)        # signal imports timeline; timeline never imports signal
```

---

## Roadmap (staged)

| Phase | Delivers |
| --- | --- |
| **1** | **`Duration` + `Instant`** — the affine line **[DONE]** |
| **2** | **`Interval` + `Coverage`** — order and supported regions **[DONE]** |
| **3** | **`Timeline` + `TimeMap`** — clocks and grounding **[DONE]** |
| **4** | **`Sampling` + `Interpolation` + discrete `Signal`** — a generic `Signal[V]` / `SampledSeries[V]` core + `Blend` typeclass, with `Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3` signal facades **[DONE]** |
| **5** | **`resample` + `Boundary`** — reconstruction and the resample axis **[DONE]** |
| 6 | `reparameterize` (affine, by a `TimeMap`: shift / slow-mo / reverse) **[DONE]**; **correspondence recovery — the exact, non-numeric half [DONE]:** `TimeMap.aligning`/`through` (offset / offset+rate from 1–2 landmarks) and the `TimeWarp` type + `TimeWarp.through(knots)` (monotonic N-knot warp) + `reparameterize(TimeWarp)`; only the estimators that *discover* correspondences from raw signals — `synchronize` / `align_to` (xcorr) and DTW — stay **[PARKED — numerics kernel that *produces* a `TimeMap`/`TimeWarp`; not "be numerics"]** |
| 7 | pointwise **lifting** (time-aligned signal algebra) **[DONE: `ScalarSignal` `+ - * /`, `Vec3Signal` `+ -`/`dot`, `Point3Signal` `displacement_to`/`distance_to`]**; advanced filters, `derivative`/`integral` **[PARKED — numerics]** |

Each phase follows the same definition of done as any primitive
([`CHECKLIST.md`](../CHECKLIST.md)): private resolver + documented facade,
`Unresolvable` for partial cases, unit + partiality + per-input propagation tests,
README/table row, `ruff` + `mypy` + `pytest --cov` (100%).

---

## Status

Phases 1–5 are implemented to the full gate: the affine line (**`Duration` +
`Instant`**), order and supported regions (**`Interval` + `Coverage`**), clocks
and grounding (**`Timeline` + `TimeMap`**), and the discrete signal layer
(**`Sampling` + `Interpolation` + `Boundary` + a generic `Signal[V]` core** with
`Scalar` / `Vec3` / `Direction3` / `Transform` / `Point3` facades) including the
**`resample`** and **`reparameterize`** (affine time-warp) axes — the latter a
*write-once* core op now shared by all five signal types. The remaining work
(`synchronize` / `align_to` + nonlinear `TimeWarp`; filters; `derivative` /
`integral`; pointwise lifting) is designed and staged above; this note is the
source to build it from.

---

## Working state & near-term plan

fungeom is the **general decidable backbone**, not a model of any one downstream
(e.g. `retarget`) — keep the primitives general; let applications compose them.
The near-term order is **breadth-first completeness, not application depth**.

**Temporal `/audit-primitives` sweep — DONE (2026-06-23).** All temporal
primitives are now audited and ticked in [`CHECKLIST.md`](../CHECKLIST.md)'s
ledger (408 tests, 100 % coverage). What was added: `Duration` `min`/`max`/
`clamp`; `Instant` `min`/`max`/`centroid`/`affine`; `Interval` `shifted`/
`expanded`; `Coverage` `difference`; `Sampling` `span`/`count`/`rate`; `Timeline`
`to_master`/`relative_to` (→ `TimeMap`); signal `restrict`/`shift` across all five
facades (one `decide_restricted` core helper + thin wrappers). **`constant(value,
over)` was deliberately deferred** — its `value` can't be parsed uniformly across
facades (Point3's frame/grounding breaks the thin-wrapper promise), so it belongs
with the per-facade value-construction story and the gappy-`Coverage` support work
below, not bolted on now. Also deferred (recorded in the ledger): `Boundary`
`wrap`/`fill`/`extend`; `Interpolation.cubic` (needs an N-point `Blend`).

**Foundational decision 1 — the `Bool` primitive — DONE (2026-06-23).** Predicates
now have a return type. A `Bool` is a first-class deferred, *decidable* truth value
(`core < boolean < scalar`): `Scalar.lt`/`le`/`gt`/`ge`, `Instant.before`/`after`,
`Interval.contains`/`overlaps`, `Coverage.contains`, and `Signal.defined_at` all
resolve *into* a `Bool`, composed with `and_`/`or_`/`not_` (`& | ~`). One generic
pair of concretes (`LessThan`/`LessEqual` over `Resolver[float]`) backs every
ordered comparison. **Propagation is strict** — `a & b` is `Unresolvable` if either
side is, uniform with every other combinator; a Kleene three-valued short-circuit
(`False & ⊥ = False`) was considered and *deliberately rejected for now* (it would
break the propagation invariant, and here `Unresolvable` means *undefined*, not
epistemic *unknown*). We still do *not* overload `__lt__`/`__gt__` (a comparison
can't return an eager `bool`); the order reductions stay `.min()`/`.max()`,
comparisons are the named `.lt()`/`.before()`/… methods.

**Foundational decision 2 — gappy `Coverage` signal support — BUILT (2026-06-23).**
Reconsidered and reversed the earlier deferral: this was not a feature to postpone
but a *correctness hole*. A signal whose samples straddle a real dropout was
silently interpolating a straight line across it — inventing data, the exact
dishonesty the decidability core forbids everywhere else. So a signal's *support*
is now an explicit gappy `Coverage`, and signals are as honest about holes as the
rest of the library.

What shipped:
- `SampledSeries` carries an explicit `support: CoverageValue` (default = the single
  `[first, last]` hull, so existing signals are unchanged).
- `sample(t)` in an interior *gap* is `Unresolvable` — the boundary policy maps only
  *past the outer edges*, never across a dropout (holding across a hole would be the
  same lie).
- Gaps are *produced* by `from_samples`/`sampled(..., max_gap=…)` (consecutive
  samples spaced beyond the threshold are not joined) and by `restrict(Coverage)`
  (which now masks the support rather than rebuilding, and can itself introduce
  gaps). `resample`/`reparameterize` carry/​warp the support honestly; resampling a
  target into a gap is `Unresolvable`.
- `support()` → `Coverage` (gap-aware), `over()` → `Interval` (the hull),
  `defined_at` = `support().contains` (now `False` inside a gap). `support`/
  `defined_at` live once on the generic `Signal[V]` base.
- Added `Boundary.wrap` (periodic) for cyclic data while in the boundary code.

Still deferred (clear, low-stakes, no design uncertainty): `Signal.constant`
(per-facade value parsing — Point3's framing breaks the thin-wrapper promise),
`Boundary.fill`/`extend`, `Interpolation.cubic` (needs an N-point `Blend`).

**Signal *lifting* (a time-aligned algebra) — BUILT (2026-06-23).** Signals now
compose pointwise: `ScalarSignal` `+ - * /` and `Vec3Signal` `+ -` (with another
signal). The resolved design:
- **Time base:** align the two operands on the **union** of their sample instants,
  clipped to the **intersection** of their supports — so the result is defined only
  where *both* are (disjoint supports → `Unresolvable`). This is exactly why lifting
  needed gappy support first.
- **Combination:** one core helper `decide_lifted(a, b, at_combined, blend)` builds
  each output value by the *ordinary static algebra* at that instant
  (`a.at(t) + b.at(t)`), so all of the static partiality flows through for free — a
  quotient is `Unresolvable` wherever the divisor crosses zero. No re-implemented
  value logic; the per-op concretes are one-liners.
- **Reconstruction:** linear between the union instants.

Chose per-op concretes + inline `at_combined` closures over a generic `map`/`zip`
with `Callable` fields — it matches the codebase's one-concrete-per-op idiom, stays
typed, keeps operands discoverable for `children()`/viz, and leaves no dead
branches. **Cross-type lifts are also done** (`Vec3Signal.dot` → `ScalarSignal`,
`Point3Signal.displacement_to` → `Vec3Signal`, `Point3Signal.distance_to` →
`ScalarSignal`): same `decide_lifted` machinery; each concrete lives in the *operand*
module and imports the *result* facade — always the acyclic direction
(`point3 → vec3 → scalar`). A quotient that crosses zero is currently *wholesale*
`Unresolvable` rather than gapped at the crossing; granular per-point gapping is a
possible later refinement.

**Correspondence recovery — the exact, non-numeric half of "sync" — BUILT
(2026-06-23).** "Synchronizing two recordings" decomposes into two halves that the
roadmap had lumped together and parked as one. The realization: a sync model is a
*map between timelines* (`time_B = a·time_A + b` is literally an `AffineTimeMap`;
drift over many landmarks is a monotonic warp), so the question splits into
*recovering the map from known correspondences* (exact algebra — fungeom's job) and
*discovering correspondences from raw signals* (xcorr / DTW — a numerics kernel,
correctly parked). The first half now exists:
- `TimeMap.aligning(source, target)` — one landmark → pure offset (unit rate); the
  known-trigger / single-clap case. Total apart from propagation.
- `TimeMap.through(first, second)` — two `(source, target)` landmarks → the exact
  affine map (offset + rate/drift): clapper at the start *and* the end.
  `Unresolvable` when the two source readings coincide (rate undetermined). Feed the
  result to `Timeline.derive` to ground a detached recording — "compute the missing
  edge", now an operation.
- **`TimeWarp`** — a new primitive: the monotonic, piecewise-linear *content* warp
  (mirrors `TimeMap`, but order-preserving and domain-limited; value
  `PiecewiseLinearWarp`). `TimeWarp.through(knots)` is the N-landmark generalization
  of `TimeMap.through` — exact, not a fitted line — `Unresolvable` for <2 or
  non-monotonic knots; `inverse` is total. Signals' `reparameterize` now accepts a
  `TimeMap | TimeWarp` (one `decide_warped` core helper), `Unresolvable` when the
  warp doesn't cover the whole signal (a warp invents no data past its knots). It
  lives at the signal tier (`signal` imports `timewarp`, never the reverse — the
  same edge that keeps affine `TimeMap` below `Signal`).

Deferred here on purpose: an N-point *least-squares* affine fit (introduces
residuals — a softer, fit-shaped notion that belongs with the numerics, not the
exact core); `TimeWarp` `identity`/`compose` (need domain-composition logic);
non-strict (plateau) warps.

**Parked (application/heavy-numerics depth — fungeom should *call* numerics, not
*be* them):** contact-reasoning slices (retarget-specific); the estimators that
*discover* correspondences — `align_to` / cross-correlation (→ a `TimeMap`) and DTW
(→ a `TimeWarp`); filters beyond a trivial `median`/`smooth`; `derivative`/
`integral` (type-changing into tangent spaces). The warp/map *types* they would
produce now exist, so these are pure numeric kernels with a ready, decidable return
type — kept thin or delegated, not hand-rolled into the core.
